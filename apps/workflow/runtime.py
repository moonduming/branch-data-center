import re
import time
from dataclasses import dataclass
from types import SimpleNamespace

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from ..organization.models import OrgUnit, UserOrgRelation
from ..users.models import User
from ..performance.models import ShenzhenPropStatus, PropStatusFlg

from .models import (
    AssigneeRuleType,
    ConditionType,
    InstanceStatus,
    NodeType,
    ProcessDefStatus,
    TaskLogAction,
    TaskResult,
    TaskStatus,
    TransitionActionCode,
    WfApprovalAssignment,
    WfInstance,
    WfNodeAssigneeRule,
    WfNodeDef,
    WfProcessDef,
    WfTask,
    WfTaskLog,
    WfTransitionDef,
)


BRANCH_KEY_PREFIX = "org_"
ACTIVE_TASK_STATUSES = [TaskStatus.PENDING, TaskStatus.PROCESSING]
APPROVED_ACTIONS = {
    TransitionActionCode.SUBMIT,
    TransitionActionCode.APPROVE,
    TransitionActionCode.COMPLETE,
}


@dataclass
class AssigneeInfo:
    """节点唯一审批人的简要信息。"""

    user_id: int
    user_name: str


class WorkflowRuntimeService:
    """工作流运行态服务，负责实例创建、节点流转和审批人解析。"""

    def __init__(self):
        """初始化运行时缓存。"""
        self._node_cache = {}
        self._rule_cache = {}
        self._user_cache = {}

    @transaction.atomic
    def start_instance(self, *, process_def_id, applicant, title=None, business_id=None):
        """创建流程实例，并为开始节点生成首个待办。"""
        process_def = WfProcessDef.objects.filter(
            id=process_def_id,
            status=ProcessDefStatus.ACTIVE,
        ).first()
        if not process_def:
            raise ValidationError({"message": "流程定义不存在或未启用"})

        start_node = self._get_start_node(process_def.id)
        now = timezone.now()
        instance = WfInstance.objects.create(
            title=title or process_def.process_name,
            process_def_id=process_def.id,
            business_type=process_def.business_type,
            business_id=business_id,
            applicant_id=applicant.id,
            applicant_name=applicant.full_name,
            current_node_code=start_node.node_code,
            current_node_name=start_node.node_name,
            status=InstanceStatus.RUNNING,
            start_time=now,
        )
        self._write_log(
            instance=instance,
            action=TaskLogAction.START,
            operator=applicant,
            to_node=start_node,
            comment="发起流程实例",
        )
        self._enter_manual_node(
            instance=instance,
            node=start_node,
            operator=applicant,
            branch_key=None,
            parallel_group=None,
        )
        return instance

    @transaction.atomic
    def handle_task_action(
        self,
        *,
        task_id,
        action_code,
        operator,
        comment=None,
        selected_user_ids=None,
        target_branch_key=None,
    ):
        """处理人工节点任务动作，并驱动后续流转。"""
        task = WfTask.objects.filter(id=task_id).first()
        if not task:
            raise ValidationError({"message": "任务不存在"})
        if task.status not in ACTIVE_TASK_STATUSES:
            raise ValidationError({"message": "当前任务已处理，不能重复操作"})
        if operator.user_level != User.Level.ADMIN and task.assignee_id != operator.id:
            raise ValidationError({"message": "只能处理分配给自己的任务"})

        instance = WfInstance.objects.filter(id=task.instance_id).first()
        if not instance or instance.status != InstanceStatus.RUNNING:
            raise ValidationError({"message": "流程实例不存在或已结束"})

        node = self._get_node(instance.process_def_id, task.node_code)
        self._validate_task_action(
            node=node,
            action_code=action_code,
            selected_user_ids=selected_user_ids,
            target_branch_key=target_branch_key,
            task=task,
        )

        transition_context = {
            "selected_user_ids": selected_user_ids or [],
            "target_branch_key": target_branch_key,
            "_trigger_action": action_code,
        }
        transitions = self._get_available_transitions(
            process_def_id=instance.process_def_id,
            from_node_code=node.node_code,
            action_code=action_code,
            context=transition_context,
        )

        result, task_status, log_action = self._map_action_result(action_code)
        to_node = None
        if len(transitions) == 1:
            to_node = self._get_node(instance.process_def_id, transitions[0].to_node_code)

        now = timezone.now()
        task.status = task_status
        task.result = result
        task.completed_at = now
        task.save(update_fields=["status", "result", "completed_at", "updated_at"])

        assignment_queryset = WfApprovalAssignment.objects.filter(task_id=task.id).order_by("-id")
        assignment = assignment_queryset.first()
        if assignment:
            assignment.result = result
            assignment.handled_at = now
            assignment.comment = comment
            assignment.save(update_fields=["result", "handled_at", "comment", "updated_at"])

        self._write_log(
            instance=instance,
            task=task,
            action=log_action,
            operator=operator,
            result=result,
            comment=comment,
            from_node=node,
            to_node=to_node,
            branch_key=task.branch_key,
            parallel_group=task.parallel_group,
        )

        if not transitions:
            if action_code == TransitionActionCode.REJECT:
                self._finish_instance(
                    instance=instance,
                    status=InstanceStatus.REJECTED,
                    operator=operator,
                    end_node=node,
                    comment=comment or "节点驳回后结束流程",
                )
                # 驳回，批量更新当前流程实例关联的占比情况表记录
                ShenzhenPropStatus.objects.filter(process_instance_id=instance.id).update(
                    prop_status_flg=PropStatusFlg.INVALID,
                    pas_data_dt=now,
                )
                return instance
            if action_code in APPROVED_ACTIONS:
                self._finish_instance(
                    instance=instance,
                    status=InstanceStatus.FINISHED,
                    operator=operator,
                    end_node=node,
                    comment=comment or "流程已结束",
                )
                return instance
            raise ValidationError({"message": f"节点[{node.node_name}]未配置动作[{action_code}]流转"})

        if node.node_type not in {NodeType.MANUAL, NodeType.START}:
            raise ValidationError({"message": "只有人工节点任务允许直接处理"})

        for transition in transitions:
            self._process_transition(
                instance=instance,
                transition=transition,
                operator=operator,
                source_task=task,
                context=transition_context,
            )
        return instance

    @transaction.atomic
    def recall_instance(self, *, instance_id, operator):
        """发起人在首个人工审核节点未处理前，将流程撤回到开始节点。"""
        instance = WfInstance.objects.filter(id=instance_id).first()
        if not instance:
            raise ValidationError({"message": "流程实例不存在"})
        if instance.status != InstanceStatus.RUNNING:
            raise ValidationError({"message": "当前流程实例不处于进行中，不能撤回"})
        if instance.applicant_id != operator.id:
            raise ValidationError({"message": "只有发起人本人可以撤回流程"})

        start_node = self._get_start_node(instance.process_def_id)
        recallable_node_codes = set(self._get_first_manual_node_codes_after_start(instance.process_def_id))
        if not recallable_node_codes:
            raise ValidationError({"message": "当前流程未配置可撤回的首个人工审核节点"})

        open_tasks = list(
            WfTask.objects.filter(
                instance_id=instance.id,
                status__in=ACTIVE_TASK_STATUSES,
            ).order_by("id")
        )
        if not open_tasks:
            raise ValidationError({"message": "当前流程没有可撤回的待处理任务"})
        if any(task.node_code == start_node.node_code for task in open_tasks):
            raise ValidationError({"message": "当前流程仍停留在开始节点，无需撤回"})
        if any(task.node_code not in recallable_node_codes for task in open_tasks):
            raise ValidationError({"message": "当前流程已流转到不可撤回阶段"})

        current_node = self._get_node(instance.process_def_id, instance.current_node_code)
        self._close_tasks(
            instance=instance,
            tasks=open_tasks,
            operator=operator,
            comment="发起人撤回流程，系统自动取消当前待办",
        )
        now = timezone.now()
        WfInstance.objects.filter(id=instance.id).update(
            current_node_code=start_node.node_code,
            current_node_name=start_node.node_name,
            status=InstanceStatus.RUNNING,
            end_time=None,
            updated_at=now,
        )
        instance.current_node_code = start_node.node_code
        instance.current_node_name = start_node.node_name
        instance.status = InstanceStatus.RUNNING
        instance.end_time = None
        self._write_log(
            instance=instance,
            action=TaskLogAction.RECALL,
            operator=operator,
            from_node=current_node,
            to_node=start_node,
            comment="发起人撤回到开始节点",
        )
        self._enter_manual_node(
            instance=instance,
            node=start_node,
            operator=operator,
            explicit_assignee=AssigneeInfo(user_id=operator.id, user_name=operator.full_name),
        )
        return instance

    def report_parallel_split(self, *, instance, node, source_task, context):
        """报表流程并行拆分：按所选用户机构一机构一分支，并将本人作为下节点处理人。"""
        grouped_users = self._collect_selected_user_orgs(context.get("selected_user_ids") or [])
        parallel_group = self._build_parallel_group(node.node_code)
        assignments = []
        for item in grouped_users:
            assignments.append(
                {
                    "branch_key": self.build_branch_key(item["org_id"]),
                    "parallel_group": parallel_group,
                    "explicit_assignee": AssigneeInfo(
                        user_id=item["user"].id,
                        user_name=item["user"].full_name,
                    ),
                }
            )
        return {
            "context": {
                "branch_count": len(assignments),
                "parallel_group": parallel_group,
            },
            "next_assignments": assignments,
        }

    def claim_parallel_split(self, *, instance, node, source_task, context):
        """认领/移交流程并行拆分：按机构建分支，下节点审批人按机构规则解析。"""
        grouped_users = self._collect_selected_user_orgs(context.get("selected_user_ids") or [])
        parallel_group = self._build_parallel_group(node.node_code)
        assignments = []
        for item in grouped_users:
            assignments.append(
                {
                    "branch_key": self.build_branch_key(item["org_id"]),
                    "parallel_group": parallel_group,
                }
            )
        return {
            "context": {
                "branch_count": len(assignments),
                "parallel_group": parallel_group,
            },
            "next_assignments": assignments,
        }

    def claim_parallel_merge_check(self, *, instance, node, source_task, context):
        """认领流程汇总判断：单分支直接结束，多分支转经办人。"""
        parallel_group = context.get("parallel_group") or getattr(source_task, "parallel_group", None)
        branch_count = self._count_parallel_branches(instance.id, parallel_group)
        has_multiple_branches = branch_count > 1
        return {
            "context": {
                "branch_count": branch_count,
                "has_multiple_branches": has_multiple_branches,
                "parallel_group": parallel_group,
            },
            "target_node_code": "perf_claim_operator_assign" if has_multiple_branches else "perf_claim_end",
        }

    def report_confirm_checker(self, *, instance, node, source_task, context):
        """报表流程自动确认单位复核节点审批人。"""
        transitions = self._get_available_transitions(
            process_def_id=instance.process_def_id,
            from_node_code=node.node_code,
            action_code=TransitionActionCode.AUTO,
            context=context,
        )
        if len(transitions) != 1:
            raise ValidationError({"message": f"自动节点[{node.node_name}]未配置唯一后续节点"})

        target_node = self._get_node(instance.process_def_id, transitions[0].to_node_code)
        assignee = self._resolve_team_based_assignee(
            instance=instance,
            node=target_node,
            branch_key=getattr(source_task, "branch_key", None),
            source_task=source_task,
        )
        return {
            "context": context,
            "next_assignments": [
                {
                    "branch_key": getattr(source_task, "branch_key", None),
                    "parallel_group": getattr(source_task, "parallel_group", None),
                    "explicit_assignee": assignee,
                }
            ],
        }

    def assign_personal_line_assignee(self, *, instance, node, source_task, context):
        """根据占比数据的条线机构自动确认下一节点审批人。"""
        transitions = self._get_available_transitions(
            process_def_id=instance.process_def_id,
            from_node_code=node.node_code,
            action_code=TransitionActionCode.AUTO,
            context=context,
        )
        if len(transitions) != 1:
            raise ValidationError({"message": f"自动节点[{node.node_name}]未配置唯一后续节点"})

        target_node = self._get_node(instance.process_def_id, transitions[0].to_node_code)
        assignee = self._resolve_personal_line_assignee(instance=instance, node=target_node)
        merged_context = dict(context or {})
        merged_context["_explicit_assignee"] = assignee
        return {
            "context": merged_context,
            "target_node_code": target_node.node_code,
        }

    def build_branch_key(self, org_id):
        """根据机构 ID 生成分支标识。"""
        return f"{BRANCH_KEY_PREFIX}{org_id}"

    def parse_branch_key(self, branch_key):
        """从分支标识中解析机构 ID。"""
        if not branch_key:
            return None
        match = re.match(r"^org_(\d+)$", branch_key)
        if not match:
            return None
        return int(match.group(1))

    def _build_parallel_group(self, node_code):
        """生成一次并行拆分对应的并行组编码。"""
        return f"{node_code}_{int(time.time() * 1000)}"

    def _get_start_node(self, process_def_id):
        """获取流程开始节点，优先取显式开始节点。"""
        nodes = self._get_process_nodes(process_def_id)
        if not nodes:
            raise ValidationError({"message": "流程未配置节点"})
        for node in nodes:
            if node.node_type == NodeType.START:
                return node
        return nodes[0]

    def _get_process_nodes(self, process_def_id):
        """按顺序加载某个流程的全部节点定义。"""
        if process_def_id not in self._node_cache:
            self._node_cache[process_def_id] = list(
                WfNodeDef.objects.filter(process_def_id=process_def_id).order_by("node_order", "id")
            )
        return self._node_cache[process_def_id]

    def _get_node(self, process_def_id, node_code):
        """按节点编码获取节点定义。"""
        for node in self._get_process_nodes(process_def_id):
            if node.node_code == node_code:
                return node
        raise ValidationError({"message": f"节点[{node_code}]不存在"})

    def _get_rule(self, process_def_id, node_code):
        """获取节点审批规则。"""
        cache_key = (process_def_id, node_code)
        if cache_key not in self._rule_cache:
            self._rule_cache[cache_key] = WfNodeAssigneeRule.objects.filter(
                process_def_id=process_def_id,
                node_code=node_code,
            ).first()
        return self._rule_cache[cache_key]

    def _get_available_transitions(self, *, process_def_id, from_node_code, action_code, context):
        """获取当前动作下可用的流转定义。"""
        transitions = WfTransitionDef.objects.filter(
            process_def_id=process_def_id,
            from_node_code=from_node_code,
            action_code=action_code,
            is_enabled=True,
        ).order_by("priority", "id")
        return [item for item in transitions if self._evaluate_transition_condition(item, context)]

    def _get_node_allowed_action_codes(self, *, process_def_id, node_code):
        """获取节点已启用流转中允许的动作编码。"""
        return list(
            WfTransitionDef.objects.filter(
                process_def_id=process_def_id,
                from_node_code=node_code,
                is_enabled=True,
            )
            .order_by("priority", "id")
            .values_list("action_code", flat=True)
            .distinct()
        )

    def _evaluate_transition_condition(self, transition, context):
        """校验流转条件，当前仅允许无条件流转。"""
        if not transition.condition_type or transition.condition_type == ConditionType.NONE:
            return True
        raise ValidationError({"message": f"暂不支持条件类型[{transition.condition_type}]"})

    def _process_transition(self, *, instance, transition, operator, source_task, context):
        """处理一条流转，并在需要时执行汇总等待逻辑。"""
        target_node = self._get_node(instance.process_def_id, transition.to_node_code)
        next_context = dict(context or {})
        explicit_assignee = next_context.pop("_explicit_assignee", None)

        if target_node.join_strategy and source_task and source_task.parallel_group and source_task.branch_key:
            if self._has_pending_parallel_sibling(source_task):
                self._write_log(
                    instance=instance,
                    task=source_task,
                    action=TaskLogAction.JOIN_PASS,
                    operator=operator,
                    from_node=self._get_node(instance.process_def_id, source_task.node_code),
                    to_node=target_node,
                    branch_key=source_task.branch_key,
                    parallel_group=source_task.parallel_group,
                    comment="当前分支已到汇总点，等待其它分支完成",
                )
                return
            next_context["parallel_group"] = source_task.parallel_group
            self._enter_node(
                instance=instance,
                node=target_node,
                operator=operator,
                source_task=source_task,
                branch_key=None,
                parallel_group=source_task.parallel_group,
                context=next_context,
                explicit_assignee=explicit_assignee,
                prefer_existing_assignee=False,
            )
            return

        branch_key = None
        parallel_group = None
        prefer_existing_assignee = False
        if source_task:
            parallel_group = source_task.parallel_group
            if transition.action_code == TransitionActionCode.RETURN:
                branch_key = next_context.get("target_branch_key") or source_task.branch_key
                prefer_existing_assignee = True
            else:
                branch_key = source_task.branch_key

        self._enter_node(
            instance=instance,
            node=target_node,
            operator=operator,
            source_task=source_task,
            branch_key=branch_key,
            parallel_group=parallel_group,
            context=next_context,
            explicit_assignee=explicit_assignee,
            prefer_existing_assignee=prefer_existing_assignee,
        )

    def _enter_node(
        self,
        *,
        instance,
        node,
        operator,
        source_task=None,
        branch_key=None,
        parallel_group=None,
        context=None,
        explicit_assignee=None,
        prefer_existing_assignee=False,
    ):
        """统一进入节点，按节点类型分发到人工、自动或结束节点。"""
        from_node = self._get_node(instance.process_def_id, source_task.node_code) if source_task else None
        if node.node_type == NodeType.END:
            self._write_log(
                instance=instance,
                task=source_task,
                action=TaskLogAction.AUTO_FLOW,
                operator=operator,
                from_node=from_node,
                to_node=node,
                branch_key=branch_key,
                parallel_group=parallel_group,
                comment="进入结束节点",
            )
            status = InstanceStatus.REJECTED if (context or {}).get("_trigger_action") == TransitionActionCode.REJECT else InstanceStatus.FINISHED
            self._finish_instance(
                instance=instance,
                status=status,
                operator=operator,
                end_node=node,
                comment="到达结束节点",
            )

            now = timezone.now()
            if status == InstanceStatus.FINISHED:
                # 完成，批量更新当前流程实例关联的占比情况表记录
                ShenzhenPropStatus.objects.filter(process_instance_id=instance.id).update(
                    prop_status_flg=PropStatusFlg.YES,
                    pas_data_dt=now,
                )

            if status == InstanceStatus.REJECTED:
                # 驳回，批量更新当前流程实例关联的占比情况表记录
                ShenzhenPropStatus.objects.filter(process_instance_id=instance.id).update(
                    prop_status_flg=PropStatusFlg.INVALID,
                    pas_data_dt=now,
                )

            return
        if node.node_type == NodeType.AUTO:
            self._write_log(
                instance=instance,
                task=source_task,
                action=TaskLogAction.AUTO_FLOW,
                operator=operator,
                from_node=from_node,
                to_node=node,
                branch_key=branch_key,
                parallel_group=parallel_group,
                comment="进入自动节点",
            )
            self._execute_auto_node(
                instance=instance,
                node=node,
                operator=operator,
                source_task=source_task,
                branch_key=branch_key,
                parallel_group=parallel_group,
                context=context,
            )
            return

        self._enter_manual_node(
            instance=instance,
            node=node,
            operator=operator,
            source_task=source_task,
            branch_key=branch_key,
            parallel_group=parallel_group,
            context=context,
            explicit_assignee=explicit_assignee,
            prefer_existing_assignee=prefer_existing_assignee,
        )

    def _execute_auto_node(self, *, instance, node, operator, source_task, branch_key, parallel_group, context):
        """执行自动节点函数，并根据函数结果决定后续出口。"""
        context = dict(context or {})
        if parallel_group and "parallel_group" not in context:
            context["parallel_group"] = parallel_group

        auto_result = {"context": context}
        if node.auto_func_name:
            func = getattr(self, node.auto_func_name, None)
            if not func:
                raise ValidationError({"message": f"自动节点函数[{node.auto_func_name}]未实现"})
            auto_result = func(instance=instance, node=node, source_task=source_task, context=context) or {"context": context}

        merged_context = dict(context)
        merged_context.update(auto_result.get("context") or {})
        transitions = self._get_available_transitions(
            process_def_id=instance.process_def_id,
            from_node_code=node.node_code,
            action_code=TransitionActionCode.AUTO,
            context=merged_context,
        )
        target_node_code = auto_result.get("target_node_code")
        if target_node_code:
            transitions = [item for item in transitions if item.to_node_code == target_node_code]

        if not transitions:
            if node.auto_func_name:
                raise ValidationError({"message": f"自动节点[{node.node_name}]未命中可用流转"})
            return

        next_assignments = auto_result.get("next_assignments") or []
        if next_assignments and len(transitions) != 1:
            raise ValidationError({"message": f"自动节点[{node.node_name}]拆分结果只支持唯一目标节点"})

        transition_source = SimpleNamespace(
            instance_id=instance.id,
            node_code=node.node_code,
            branch_key=branch_key,
            parallel_group=parallel_group,
            id=getattr(source_task, "id", None),
        )
        if next_assignments:
            transition = transitions[0]
            target_node = self._get_node(instance.process_def_id, transition.to_node_code)
            for item in next_assignments:
                self._enter_node(
                    instance=instance,
                    node=target_node,
                    operator=operator,
                    source_task=transition_source,
                    branch_key=item.get("branch_key"),
                    parallel_group=item.get("parallel_group"),
                    context=merged_context,
                    explicit_assignee=item.get("explicit_assignee"),
                    prefer_existing_assignee=False,
                )
            return

        for transition in transitions:
            self._process_transition(
                instance=instance,
                transition=transition,
                operator=operator,
                source_task=transition_source,
                context=merged_context,
            )

    def _enter_manual_node(
        self,
        *,
        instance,
        node,
        operator,
        source_task=None,
        branch_key=None,
        parallel_group=None,
        context=None,
        explicit_assignee=None,
        prefer_existing_assignee=False,
    ):
        """进入需要人工处理的节点，并创建待办和审批分配。"""
        assignee = explicit_assignee
        if assignee is None and prefer_existing_assignee:
            assignee = self._find_history_assignee(
                instance_id=instance.id,
                node_code=node.node_code,
                branch_key=branch_key,
            )
        if assignee is None:
            assignee = self._resolve_node_assignee(
                instance=instance,
                node=node,
                branch_key=branch_key,
                source_task=source_task,
            )
        
        task = WfTask.objects.create(
            instance_id=instance.id,
            node_code=node.node_code,
            node_name=node.node_name,
            assignee_id=assignee.user_id,
            assignee_name=assignee.user_name,
            branch_key=branch_key,
            parallel_group=parallel_group,
            status=TaskStatus.PENDING,
            round_no=self._next_round_no(instance.id, node.node_code, branch_key),
        )
        WfApprovalAssignment.objects.create(
            instance_id=instance.id,
            task_id=task.id,
            node_code=node.node_code,
            node_name=node.node_name,
            assignee_id=assignee.user_id,
            assignee_name=assignee.user_name,
            round_no=task.round_no,
            received_at=timezone.now(),
        )
        WfInstance.objects.filter(id=instance.id).update(
            current_node_code=node.node_code,
            current_node_name=node.node_name,
            updated_at=timezone.now(),
        )
        instance.current_node_code = node.node_code
        instance.current_node_name = node.node_name
        self._write_log(
            instance=instance,
            task=task,
            action=TaskLogAction.CREATE_TASK,
            operator=operator,
            from_node=self._get_node(instance.process_def_id, source_task.node_code) if source_task else None,
            to_node=node,
            branch_key=branch_key,
            parallel_group=parallel_group,
            comment="创建待办任务",
        )

    def _resolve_org_id(self, *, instance, branch_key=None, source_task=None):
        """解析节点审批使用的机构 ID。"""
        org_id = self.parse_branch_key(branch_key)
        if org_id is None:
            org_id = self._resolve_org_id_from_source_task(source_task)
        if org_id is None:
            relation = self._get_user_primary_relation(instance.applicant_id)
            org_id = relation.org_id
        return org_id

    def _get_employee_level_codes(self, *, rule, node):
        """解析员工级别规则配置。"""
        level_codes = [item.strip() for item in (rule.rule_value or "").split(",") if item.strip()]
        if not level_codes:
            raise ValidationError({"message": f"节点[{node.node_name}]未配置员工级别"})
        return level_codes

    def _list_rule_matched_users(self, *, org_id, level_codes, extra_filters=None):
        """按机构、员工级别和附加条件查找可用审批人。"""
        filter_kwargs = {
            "org_id": org_id,
            "status": UserOrgRelation.Status.NORMAL,
            "employee_level__in": level_codes,
        }
        if extra_filters:
            filter_kwargs.update(extra_filters)

        user_ids = (
            UserOrgRelation.objects.filter(**filter_kwargs)
            .values_list("user_id", flat=True)
            .distinct()
        )
        return User.objects.filter(id__in=user_ids, user_status=User.Status.NORMAL)

    def _get_source_task_assignee_id(self, source_task):
        """获取来源任务的审批人 ID。"""
        if not source_task:
            return None
        assignee_id = getattr(source_task, "assignee_id", None)
        if assignee_id is not None:
            return assignee_id
        task_id = getattr(source_task, "id", None)
        if not task_id:
            return None
        history_task = WfTask.objects.filter(id=task_id).first()
        return getattr(history_task, "assignee_id", None)

    def _resolve_team_based_assignee(self, *, instance, node, branch_key=None, source_task=None):
        """按上一节点审批人的团队 + 当前机构 + 目标节点规则解析审批人。"""
        rule = self._get_rule(instance.process_def_id, node.node_code)
        if not rule:
            raise ValidationError({"message": f"节点[{node.node_name}]未配置审批人规则，请管理员配置"})
        if rule.rule_type != AssigneeRuleType.EMPLOYEE_LEVEL:
            return self._resolve_node_assignee(
                instance=instance,
                node=node,
                branch_key=branch_key,
                source_task=source_task,
            )

        org_id = self._resolve_org_id(instance=instance, branch_key=branch_key, source_task=source_task)
        level_codes = self._get_employee_level_codes(rule=rule, node=node)
        source_assignee_id = self._get_source_task_assignee_id(source_task)
        if source_assignee_id is None:
            raise ValidationError({"message": f"节点[{node.node_name}]无法确认上一节点审批人，请管理员配置"})

        source_relation = (
            UserOrgRelation.objects.filter(
                user_id=source_assignee_id,
                org_id=org_id,
                status=UserOrgRelation.Status.NORMAL,
            )
            .order_by("-is_primary", "id")
            .first()
        )
        if not source_relation:
            raise ValidationError({"message": f"节点[{node.node_name}]无法确认上一节点审批人的团队，请管理员配置"})

        team_filters = {"team_name": source_relation.team_name}
        if not team_filters:
            raise ValidationError({"message": f"节点[{node.node_name}]无法确认上一节点审批人的团队，请管理员配置"})

        matched_users = self._list_rule_matched_users(
            org_id=org_id,
            level_codes=level_codes,
            extra_filters=team_filters,
        )
        if not matched_users:
            raise ValidationError({"message": f"节点[{node.node_name}]未找到符合条件的审批人，请管理员配置"})

        user = matched_users[0]
        return AssigneeInfo(user_id=user.id, user_name=user.full_name)

    def _resolve_personal_line_assignee(self, *, instance, node):
        """按条线机构和个人条线团队解析唯一审批人。"""
        line_org_code = self._get_instance_line_org_code(instance.id)
        org = OrgUnit.objects.filter(
            org_code=line_org_code,
            status=OrgUnit.Status.NORMAL,
        ).first()
        if not org:
            raise ValidationError({"message": f"节点[{node.node_name}]未找到条线机构[{line_org_code}]，请管理员配置"})

        user_ids = list(
            UserOrgRelation.objects.filter(
                org_id=org.id,
                status=UserOrgRelation.Status.NORMAL,
                team_name__icontains="条线审批人",
            )
            .order_by("-is_primary", "id")
            .values_list("user_id", flat=True)
            .distinct()
        )
        if not user_ids:
            raise ValidationError({"message": f"节点[{node.node_name}]未找到个人条线审批人，请管理员配置"})

        matched_users = list(User.objects.filter(id__in=user_ids, user_status=User.Status.NORMAL).order_by("id"))
        if not matched_users:
            raise ValidationError({"message": f"节点[{node.node_name}]未找到个人条线审批人，请管理员配置"})
        if len(matched_users) > 1:
            raise ValidationError({"message": f"节点[{node.node_name}]找到多个个人条线审批人，请管理员修改配置"})

        user = matched_users[0]
        return AssigneeInfo(user_id=user.id, user_name=user.full_name)

    def _resolve_node_assignee(self, *, instance, node, branch_key=None, source_task=None):
        """按节点审批规则解析唯一审批人。"""
        rule = self._get_rule(instance.process_def_id, node.node_code)
        if not rule:
            raise ValidationError({"message": f"节点[{node.node_name}]未配置审批人规则"})

        if rule.rule_type == AssigneeRuleType.APPLICANT:
            self._validate_single_rule_user(rule, node)
            user = self._get_user(instance.applicant_id)
            return AssigneeInfo(user_id=user.id, user_name=user.full_name)

        if rule.rule_type == AssigneeRuleType.FIXED_USER:
            user_id = self._validate_single_rule_user(rule, node, required=True)
            user = self._get_user(user_id)
            return AssigneeInfo(user_id=user.id, user_name=user.full_name)

        if rule.rule_type != AssigneeRuleType.EMPLOYEE_LEVEL:
            raise ValidationError({"message": f"节点[{node.node_name}]存在不支持的审批人类型[{rule.rule_type}]"})

        org_id = self._resolve_org_id(instance=instance, branch_key=branch_key, source_task=source_task)
        level_codes = self._get_employee_level_codes(rule=rule, node=node)
        matched_users = self._list_rule_matched_users(
            org_id=org_id,
            level_codes=level_codes,
        )

        if not matched_users:
            raise ValidationError({"message": f"节点[{node.node_name}]没有审批人，请管理员修改节点审批规则"})
        if len(matched_users) > 1:
            raise ValidationError({"message": f"节点[{node.node_name}]有多个审批人，请管理员修改节点审批规则"})

        user = matched_users[0]
        return AssigneeInfo(user_id=user.id, user_name=user.full_name)

    def _get_instance_line_org_code(self, instance_id):
        """获取流程实例关联占比数据中的条线机构编码。"""
        line_org_code = (
            ShenzhenPropStatus.objects.filter(process_instance_id=instance_id)
            .exclude(line_org_code__isnull=True)
            .exclude(line_org_code="")
            .order_by("id")
            .values_list("line_org_code", flat=True)
            .first()
        )
        if not line_org_code:
            raise ValidationError({"message": "流程实例未找到条线机构编码"})
        return line_org_code

    def _resolve_org_id_from_source_task(self, source_task):
        """当 branch_key 不可用时，从上一个节点审核人的主归属机构推导机构 ID。"""
        if not source_task:
            return None

        assignee_id = getattr(source_task, "assignee_id", None)
        if assignee_id is None and getattr(source_task, "id", None):
            history_task = WfTask.objects.filter(id=source_task.id).first()
            assignee_id = getattr(history_task, "assignee_id", None)
        if assignee_id is None:
            return None

        relation = self._get_user_primary_relation(assignee_id)
        return relation.org_id

    def _validate_single_rule_user(self, rule, node, required=False):
        """校验规则值中只配置了一个用户 ID。"""
        values = [item.strip() for item in (rule.rule_value or "").split(",") if item.strip()]
        if len(values) > 1:
            raise ValidationError({"message": f"节点[{node.node_name}]有多个审批人，请管理员修改节点审批规则"})
        if required and not values:
            raise ValidationError({"message": f"节点[{node.node_name}]没有审批人，请管理员修改节点审批规则"})
        if not values:
            return None
        try:
            return int(values[0])
        except (TypeError, ValueError) as exc:
            raise ValidationError({"message": f"节点[{node.node_name}]审批人配置不是有效用户ID"}) from exc

    def _get_user(self, user_id):
        """获取有效用户。"""
        if user_id not in self._user_cache:
            self._user_cache[user_id] = User.objects.filter(id=user_id, user_status=User.Status.NORMAL).first()
        user = self._user_cache[user_id]
        if not user:
            raise ValidationError({"message": "用户不存在或不可用"})
        return user

    def _get_user_primary_relation(self, user_id):
        """获取用户主归属机构关系。"""
        relations = list(
            UserOrgRelation.objects.filter(
                user_id=user_id,
                status=UserOrgRelation.Status.NORMAL,
            ).order_by("-is_primary", "id")
        )
        if not relations:
            raise ValidationError({"message": "用户未配置所属机构"})
        primary_relations = [item for item in relations if item.is_primary]
        if len(primary_relations) == 1:
            return primary_relations[0]
        if len(relations) == 1:
            return relations[0]
        raise ValidationError({"message": "用户存在多个所属机构，请维护主归属机构"})

    def _find_history_assignee(self, *, instance_id, node_code, branch_key):
        """查询同实例同节点同分支上一次的处理人。"""
        history_task = (
            WfTask.objects.filter(
                instance_id=instance_id,
                node_code=node_code,
                branch_key=branch_key,
                assignee_id__isnull=False,
            )
            .order_by("-id")
            .first()
        )
        if not history_task:
            return None
        return AssigneeInfo(user_id=history_task.assignee_id, user_name=history_task.assignee_name)

    def _next_round_no(self, instance_id, node_code, branch_key):
        """计算节点当前审批轮次。"""
        last_task = (
            WfTask.objects.filter(instance_id=instance_id, node_code=node_code, branch_key=branch_key)
            .order_by("-round_no", "-id")
            .first()
        )
        return (last_task.round_no if last_task else 0) + 1

    def _get_first_manual_node_codes_after_start(self, process_def_id):
        """获取开始节点提交后最先到达的人工节点集合。"""
        start_node = self._get_start_node(process_def_id)
        pending_node_codes = [start_node.node_code]
        visited = set()
        manual_node_codes = []

        while pending_node_codes:
            node_code = pending_node_codes.pop(0)
            if node_code in visited:
                continue
            visited.add(node_code)
            node = self._get_node(process_def_id, node_code)

            if node_code != start_node.node_code and node.node_type == NodeType.MANUAL:
                manual_node_codes.append(node_code)
                continue
            if node.node_type == NodeType.END:
                continue

            action_code = TransitionActionCode.AUTO if node.node_type == NodeType.AUTO else TransitionActionCode.SUBMIT
            transitions = self._get_available_transitions(
                process_def_id=process_def_id,
                from_node_code=node.node_code,
                action_code=action_code,
                context={},
            )
            pending_node_codes.extend(item.to_node_code for item in transitions)

        return manual_node_codes

    def _has_pending_parallel_sibling(self, source_task):
        """判断并行组内是否还有未完成的兄弟分支。"""
        queryset = WfTask.objects.filter(
            instance_id=source_task.instance_id,
            parallel_group=source_task.parallel_group,
            status__in=ACTIVE_TASK_STATUSES,
        )
        if source_task.branch_key:
            queryset = queryset.exclude(branch_key=source_task.branch_key)
        else:
            queryset = queryset.exclude(id=source_task.id)
        return queryset.exists()

    def _count_parallel_branches(self, instance_id, parallel_group):
        """统计某个并行组下的机构分支数量。"""
        if not parallel_group:
            return 0
        return (
            WfTask.objects.filter(instance_id=instance_id, parallel_group=parallel_group)
            .exclude(branch_key__isnull=True)
            .exclude(branch_key="")
            .values("branch_key")
            .distinct()
            .count()
        )

    def _collect_selected_user_orgs(self, selected_user_ids):
        """收集发起节点所选用户，并校验一机构只能选择一人。"""
        user_ids = []
        for item in selected_user_ids or []:
            try:
                user_ids.append(int(item))
            except (TypeError, ValueError) as exc:
                raise ValidationError({"selected_user_ids": ["发起节点选择的用户ID不合法"]}) from exc
        if not user_ids:
            raise ValidationError({"selected_user_ids": ["发起节点必须选择用户"]})
        if len(user_ids) != len(set(user_ids)):
            raise ValidationError({"selected_user_ids": ["存在重复选择的用户"]})

        grouped = []
        used_org_ids = set()
        for user_id in user_ids:
            user = self._get_user(user_id)
            relation = self._get_user_primary_relation(user_id)
            org = OrgUnit.objects.filter(id=relation.org_id, status=OrgUnit.Status.NORMAL).first()
            if not org:
                raise ValidationError({"message": f"用户[{user.full_name}]所属机构不存在或不可用"})
            if org.id in used_org_ids:
                raise ValidationError({"message": "所选用户存在相同机构，请重新选择，保证一个机构只对应一个并行分支"})
            used_org_ids.add(org.id)
            grouped.append(
                {
                    "user": user,
                    "relation": relation,
                    "org_id": org.id,
                    "org_name": org.org_name,
                }
            )
        return grouped

    def _validate_task_action(self, *, node, action_code, selected_user_ids, target_branch_key, task):
        """校验当前任务动作是否合法。"""
        start_node = self._get_start_node(node.process_def_id)
        allowed_action_codes = self._get_node_allowed_action_codes(
            process_def_id=node.process_def_id,
            node_code=node.node_code,
        )
        if action_code not in allowed_action_codes:
            action_label_map = dict(TransitionActionCode.choices)
            allowed_action_text = "、".join(
                f"{action_label_map.get(code, code)}({code})" for code in allowed_action_codes
            )
            if not allowed_action_text:
                allowed_action_text = "无可用动作"
            raise ValidationError(
                {"message": f"节点[{node.node_name}]不允许执行动作[{action_code}]，当前只能使用：{allowed_action_text}"}
            )
        if action_code == TransitionActionCode.REJECT and not node.can_reject:
            raise ValidationError({"message": f"节点[{node.node_name}]不允许驳回"})
        if action_code == TransitionActionCode.RETURN and not node.can_return:
            raise ValidationError({"message": f"节点[{node.node_name}]不允许退回"})
        if action_code == TransitionActionCode.SUBMIT and node.node_code == start_node.node_code:
            if not selected_user_ids:
                raise ValidationError({"selected_user_ids": ["发起节点必须选择用户"]})
        if action_code == TransitionActionCode.RETURN and task.parallel_group and not task.branch_key and not target_branch_key:
            raise ValidationError({"target_branch_key": ["当前汇总节点退回时必须指定退回分支"]})

    def _map_action_result(self, action_code):
        """将动作编码映射为任务结果和日志动作。"""
        if action_code in APPROVED_ACTIONS:
            return TaskResult.AGREE, TaskStatus.APPROVED, TaskLogAction.APPROVE
        if action_code == TransitionActionCode.REJECT:
            return TaskResult.REJECT, TaskStatus.REJECTED, TaskLogAction.REJECT
        if action_code == TransitionActionCode.RETURN:
            return TaskResult.RETURN, TaskStatus.RETURNED, TaskLogAction.RETURN
        raise ValidationError({"message": f"不支持的任务动作[{action_code}]"})

    def _close_tasks(self, *, instance, tasks, operator, comment):
        """关闭一批活动任务，并补齐审批分配与日志。"""
        task_list = list(tasks)
        if not task_list:
            return

        now = timezone.now()
        task_ids = [item.id for item in task_list]
        WfTask.objects.filter(id__in=task_ids).update(
            status=TaskStatus.CANCELLED,
            result=TaskResult.AUTO_SKIP,
            completed_at=now,
            updated_at=now,
        )
        WfApprovalAssignment.objects.filter(task_id__in=task_ids, handled_at__isnull=True).update(
            result=TaskResult.AUTO_SKIP,
            handled_at=now,
            comment=comment,
            updated_at=now,
        )
        for item in task_list:
            self._write_log(
                instance=instance,
                task=item,
                action=TaskLogAction.CANCEL_TASK,
                operator=operator,
                from_node=self._get_node(instance.process_def_id, item.node_code),
                branch_key=item.branch_key,
                parallel_group=item.parallel_group,
                result=TaskResult.AUTO_SKIP,
                comment=comment,
            )

    def _finish_instance(self, *, instance, status, operator, end_node, comment):
        """结束流程实例，并自动关闭其他未处理待办。"""
        now = timezone.now()
        WfInstance.objects.filter(id=instance.id).update(
            current_node_code=getattr(end_node, "node_code", None),
            current_node_name=getattr(end_node, "node_name", None),
            status=status,
            end_time=now,
            updated_at=now,
        )
        instance.current_node_code = getattr(end_node, "node_code", None)
        instance.current_node_name = getattr(end_node, "node_name", None)
        instance.status = status
        instance.end_time = now

        open_tasks = list(
            WfTask.objects.filter(
                instance_id=instance.id,
                status__in=ACTIVE_TASK_STATUSES,
            ).order_by("id")
        )
        self._close_tasks(
            instance=instance,
            tasks=open_tasks,
            operator=operator,
            comment="流程结束，系统自动取消待办",
        )

        self._write_log(
            instance=instance,
            action=TaskLogAction.FINISH,
            operator=operator,
            to_node=end_node,
            result=TaskResult.REJECT if status == InstanceStatus.REJECTED else TaskResult.AUTO_PASS,
            comment=comment,
        )

    def _write_log(
        self,
        *,
        instance,
        action,
        operator,
        task=None,
        from_node=None,
        to_node=None,
        branch_key=None,
        parallel_group=None,
        result=None,
        comment=None,
    ):
        """写入一条流程运行日志。"""
        WfTaskLog.objects.create(
            instance_id=instance.id,
            task_id=getattr(task, "id", None),
            action=action,
            from_node_code=getattr(from_node, "node_code", None),
            from_node_name=getattr(from_node, "node_name", None),
            to_node_code=getattr(to_node, "node_code", None),
            to_node_name=getattr(to_node, "node_name", None),
            operator_id=getattr(operator, "id", None),
            operator_name=getattr(operator, "full_name", None),
            branch_key=branch_key,
            parallel_group=parallel_group,
            result=result,
            comment=comment,
        )
