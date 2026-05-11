from django.db import transaction
from django.db.models import Count, Q
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.organization.models import OrgUnit
from apps.performance.models import ShenzhenPropStatus
from apps.performance.serializers import ShenzhenPropStatusSerializer
from apps.users.models import User
from common.permissions import IsAdminUserLevel
from common.query import parse_bool_param, parse_optional_int_param

from .models import (
    AssigneeRuleType,
    ConditionType,
    JoinStrategy,
    NodeType,
    ProcessBusinessType,
    ProcessDefStatus,
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
from .runtime import WorkflowRuntimeService
from .serializers import (
    WfApprovalAssignmentSerializer,
    WfInstanceSerializer,
    WfInstanceStartSerializer,
    WfNodeAssigneeRuleSerializer,
    WfNodeDefSerializer,
    WfProcessDefSerializer,
    WfTaskActionSerializer,
    WfTaskLogSerializer,
    WfTaskSerializer,
    WfTransitionDefSerializer,
    _get_next_process_version,
)


def success_response(data, message="查询成功", status_code=status.HTTP_200_OK):
    return Response({"message": message, "data": data}, status=status_code)


def choice_items(choices, descriptions=None):
    descriptions = descriptions or {}
    items = []
    for value, label in choices:
        item = {"value": value, "label": label}
        if value in descriptions:
            item["description"] = descriptions[value]
        items.append(item)
    return items


def boolean_choice_items(true_label="是", false_label="否"):
    return [
        {"value": True, "label": true_label},
        {"value": False, "label": false_label},
    ]


def build_process_count_map(process_def_ids, model):
    if not process_def_ids:
        return {}
    return {
        item["process_def_id"]: item["count"]
        for item in model.objects.filter(process_def_id__in=process_def_ids)
        .values("process_def_id")
        .annotate(count=Count("id"))
    }

PROCESS_STATUS_LABEL_MAP = dict(ProcessDefStatus.choices)


def build_node_name_map(process_def_ids):
    if not process_def_ids:
        return {}
    return {
        (item["process_def_id"], item["node_code"]): item["node_name"]
        for item in WfNodeDef.objects.filter(process_def_id__in=process_def_ids).values(
            "process_def_id",
            "node_code",
            "node_name",
        )
    }


def has_process_instances(process_def_id):
    return WfInstance.objects.filter(process_def_id=process_def_id).exists()


def parse_branch_org_id(branch_key):
    if not branch_key or not str(branch_key).startswith("org_"):
        return None
    try:
        return int(str(branch_key).split("_", 1)[1])
    except (TypeError, ValueError):
        return None


class WorkflowBaseViewSet(viewsets.ModelViewSet):
    """
    工作流基础视图集
    """
    permission_classes = [IsAdminUserLevel]

    def attach_related_info(self, objects):
        return list(objects)

    def validate_update_allowed(self, instance):
        return None

    def validate_destroy_allowed(self, instance):
        return None

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            objects = self.attach_related_info(page)
            serializer = self.get_serializer(objects, many=True)
            return self.get_paginated_response(serializer.data)

        objects = self.attach_related_info(queryset)
        serializer = self.get_serializer(objects, many=True)
        return Response({"message": "查询成功", "data": serializer.data})

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        self.attach_related_info([instance])
        serializer = self.get_serializer(instance)
        return Response({"message": "查询成功", "data": serializer.data})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        self.attach_related_info([serializer.instance])
        output_serializer = self.get_serializer(serializer.instance)
        headers = self.get_success_headers(output_serializer.data)
        response = Response({"message": "创建成功", "data": output_serializer.data}, status=status.HTTP_201_CREATED)
        for key, value in headers.items():
            response[key] = value
        return response

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        self.validate_update_allowed(instance)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        self.attach_related_info([serializer.instance])
        output_serializer = self.get_serializer(serializer.instance)

        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}

        return Response({"message": "更新成功", "data": output_serializer.data})

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.validate_destroy_allowed(instance)
        self.perform_destroy(instance)
        return Response({"message": "删除成功", "data": None})


class WfProcessDefViewSet(WorkflowBaseViewSet):
    """流程定义表视图"""
    queryset = WfProcessDef.objects.all().order_by("-is_latest", "process_code", "-version", "-id")
    serializer_class = WfProcessDefSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        process_code = self.request.query_params.get("process_code")
        process_name = self.request.query_params.get("process_name")
        business_type = self.request.query_params.get("business_type")
        status_value = self.request.query_params.get("status")
        is_latest = parse_bool_param(self.request.query_params.get("is_latest"))

        if process_code:
            queryset = queryset.filter(process_code__icontains=process_code)
        if process_name:
            queryset = queryset.filter(process_name__icontains=process_name)
        if business_type:
            queryset = queryset.filter(business_type=business_type)
        if status_value:
            queryset = queryset.filter(status=status_value)
        if is_latest is not None:
            queryset = queryset.filter(is_latest=is_latest)
        return queryset

    def attach_related_info(self, objects):
        process_defs = list(objects)
        if not process_defs:
            return process_defs

        process_def_ids = [item.id for item in process_defs]
        node_counts = {
            item["process_def_id"]: item["count"]
            for item in WfNodeDef.objects.filter(process_def_id__in=process_def_ids)
            .values("process_def_id")
            .annotate(count=Count("id"))
        }
        assignee_rule_counts = {
            item["process_def_id"]: item["count"]
            for item in WfNodeAssigneeRule.objects.filter(process_def_id__in=process_def_ids)
            .values("process_def_id")
            .annotate(count=Count("id"))
        }
        transition_counts = {
            item["process_def_id"]: item["count"]
            for item in WfTransitionDef.objects.filter(process_def_id__in=process_def_ids)
            .values("process_def_id")
            .annotate(count=Count("id"))
        }

        for item in process_defs:
            item.node_count = node_counts.get(item.id, 0)
            item.assignee_rule_count = assignee_rule_counts.get(item.id, 0)
            item.transition_count = transition_counts.get(item.id, 0)
        return process_defs

    def validate_update_allowed(self, instance):
        if has_process_instances(instance.id):
            raise ValidationError({"message": "当前流程定义已创建流程实例，不允许修改"})

    def validate_destroy_allowed(self, instance):
        if has_process_instances(instance.id):
            raise ValidationError({"message": "当前流程定义已创建流程实例，不允许删除"})

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.validate_destroy_allowed(instance)
        dependency_parts = []

        node_count = WfNodeDef.objects.filter(process_def_id=instance.id).count()
        if node_count:
            dependency_parts.append(f"节点定义 {node_count} 条")

        assignee_rule_count = WfNodeAssigneeRule.objects.filter(process_def_id=instance.id).count()
        if assignee_rule_count:
            dependency_parts.append(f"节点审核员规则 {assignee_rule_count} 条")

        transition_count = WfTransitionDef.objects.filter(process_def_id=instance.id).count()
        if transition_count:
            dependency_parts.append(f"流转定义 {transition_count} 条")

        if dependency_parts:
            raise ValidationError({"message": f"当前流程定义仍关联{', '.join(dependency_parts)}，请先删除关联数据后再删除"})
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"], url_path="copy")
    def copy(self, request, *args, **kwargs):
        source_process_def = self.get_object()
        with transaction.atomic():
            target_process_def = WfProcessDef.objects.create(
                process_code=source_process_def.process_code,
                process_name=source_process_def.process_name,
                business_type=source_process_def.business_type,
                version=_get_next_process_version(source_process_def.process_code),
                status=source_process_def.status,
                is_latest=True,
                remark=source_process_def.remark,
            )

            source_nodes = list(
                WfNodeDef.objects.filter(process_def_id=source_process_def.id).order_by("node_order", "id")
            )
            source_rules = list(
                WfNodeAssigneeRule.objects.filter(process_def_id=source_process_def.id).order_by("id")
            )
            source_transitions = list(
                WfTransitionDef.objects.filter(process_def_id=source_process_def.id).order_by("priority", "id")
            )

            WfProcessDefSerializer._sync_latest_flag(target_process_def.process_code, target_process_def.id)

            if source_nodes:
                WfNodeDef.objects.bulk_create(
                    [
                        WfNodeDef(
                            process_def_id=target_process_def.id,
                            node_code=item.node_code,
                            node_name=item.node_name,
                            node_type=item.node_type,
                            auto_func_name=item.auto_func_name,
                            node_order=item.node_order,
                            is_parallel=item.is_parallel,
                            parallel_mode=item.parallel_mode,
                            join_strategy=item.join_strategy,
                            can_reject=item.can_reject,
                            can_return=item.can_return,
                            auto_create_task=item.auto_create_task,
                            remark=item.remark,
                        )
                        for item in source_nodes
                    ]
                )

            if source_rules:
                WfNodeAssigneeRule.objects.bulk_create(
                    [
                        WfNodeAssigneeRule(
                            process_def_id=target_process_def.id,
                            node_code=item.node_code,
                            rule_type=item.rule_type,
                            rule_value=item.rule_value,
                            remark=item.remark,
                        )
                        for item in source_rules
                    ]
                )

            if source_transitions:
                WfTransitionDef.objects.bulk_create(
                    [
                        WfTransitionDef(
                            process_def_id=target_process_def.id,
                            from_node_code=item.from_node_code,
                            to_node_code=item.to_node_code,
                            action_code=item.action_code,
                            condition_type=item.condition_type,
                            condition_expr=item.condition_expr,
                            priority=item.priority,
                            is_enabled=item.is_enabled,
                            remark=item.remark,
                        )
                        for item in source_transitions
                    ]
                )

        process_data = self.get_serializer(target_process_def).data
        data = {
            "process_def": process_data,
            "copied_counts": {
                "node_count": len(source_nodes),
                "assignee_rule_count": len(source_rules),
                "transition_count": len(source_transitions),
            },
            "source_process_def_id": source_process_def.id,
        }
        return success_response(data, message="复制成功", status_code=status.HTTP_201_CREATED)


class WfNodeDefViewSet(WorkflowBaseViewSet):
    """流程节点定义视图"""
    queryset = WfNodeDef.objects.all().order_by("process_def_id", "node_order", "id")
    serializer_class = WfNodeDefSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        process_def_id = parse_optional_int_param(self.request.query_params.get("process_def_id"), "process_def_id")
        node_code = self.request.query_params.get("node_code")
        node_name = self.request.query_params.get("node_name")
        node_type = self.request.query_params.get("node_type")
        join_strategy = self.request.query_params.get("join_strategy")
        is_parallel = parse_bool_param(self.request.query_params.get("is_parallel"))

        if "pk" not in getattr(self, "kwargs", {}):
            if process_def_id is None:
                raise ValidationError({"process_def_id": ["该参数必填"]})
            queryset = queryset.filter(process_def_id=process_def_id)
        if node_code:
            queryset = queryset.filter(node_code__icontains=node_code)
        if node_name:
            queryset = queryset.filter(node_name__icontains=node_name)
        if node_type:
            queryset = queryset.filter(node_type=node_type)
        if join_strategy:
            queryset = queryset.filter(join_strategy=join_strategy)
        if is_parallel is not None:
            queryset = queryset.filter(is_parallel=is_parallel)
        return queryset

    def validate_update_allowed(self, instance):
        if has_process_instances(instance.process_def_id):
            raise ValidationError({"message": "当前流程已创建流程实例，不允许修改节点定义"})

    def validate_destroy_allowed(self, instance):
        if has_process_instances(instance.process_def_id):
            raise ValidationError({"message": "当前流程已创建流程实例，不允许删除节点定义"})

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.validate_destroy_allowed(instance)
        dependency_parts = []

        assignee_rule_count = WfNodeAssigneeRule.objects.filter(
            process_def_id=instance.process_def_id,
            node_code=instance.node_code,
        ).count()
        if assignee_rule_count:
            dependency_parts.append(f"节点审核员规则 {assignee_rule_count} 条")

        transition_count = WfTransitionDef.objects.filter(process_def_id=instance.process_def_id).filter(
            Q(from_node_code=instance.node_code) | Q(to_node_code=instance.node_code)
        ).count()
        if transition_count:
            dependency_parts.append(f"流转定义 {transition_count} 条")

        if dependency_parts:
            raise ValidationError({"message": f"当前节点仍关联{', '.join(dependency_parts)}，请先删除关联数据后再删除"})
        return super().destroy(request, *args, **kwargs)


class WfTransitionDefViewSet(WorkflowBaseViewSet):
    """流程流转定义视图"""
    queryset = WfTransitionDef.objects.all().order_by("process_def_id", "priority", "id")
    serializer_class = WfTransitionDefSerializer

    def validate_update_allowed(self, instance):
        if has_process_instances(instance.process_def_id):
            raise ValidationError({"message": "当前流程已创建流程实例，不允许修改流转定义"})

    def validate_destroy_allowed(self, instance):
        if has_process_instances(instance.process_def_id):
            raise ValidationError({"message": "当前流程已创建流程实例，不允许删除流转定义"})

    def get_queryset(self):
        queryset = super().get_queryset()
        process_def_id = parse_optional_int_param(self.request.query_params.get("process_def_id"), "process_def_id")
        from_node_code = self.request.query_params.get("from_node_code")
        to_node_code = self.request.query_params.get("to_node_code")
        action_code = self.request.query_params.get("action_code")
        condition_type = self.request.query_params.get("condition_type")
        is_enabled = parse_bool_param(self.request.query_params.get("is_enabled"))

        if "pk" not in getattr(self, "kwargs", {}):
            if process_def_id is None:
                raise ValidationError({"process_def_id": ["该参数必填"]})
            queryset = queryset.filter(process_def_id=process_def_id)
        if from_node_code:
            queryset = queryset.filter(from_node_code=from_node_code)
        if to_node_code:
            queryset = queryset.filter(to_node_code=to_node_code)
        if action_code:
            queryset = queryset.filter(action_code=action_code)
        if condition_type:
            queryset = queryset.filter(condition_type=condition_type)
        if is_enabled is not None:
            queryset = queryset.filter(is_enabled=is_enabled)
        return queryset

    def attach_related_info(self, objects):
        transitions = list(objects)
        if not transitions:
            return transitions

        node_map = build_node_name_map({item.process_def_id for item in transitions if item.process_def_id is not None})

        for item in transitions:
            item.from_node_name = node_map.get((item.process_def_id, item.from_node_code))
            item.to_node_name = node_map.get((item.process_def_id, item.to_node_code))
        return transitions


class WfNodeAssigneeRuleViewSet(WorkflowBaseViewSet):
    """节点审核人规则视图"""
    queryset = WfNodeAssigneeRule.objects.all().order_by("process_def_id", "node_code", "id")
    serializer_class = WfNodeAssigneeRuleSerializer

    def validate_update_allowed(self, instance):
        if has_process_instances(instance.process_def_id):
            raise ValidationError({"message": "当前流程已创建流程实例，不允许修改节点审核人规则"})

    def validate_destroy_allowed(self, instance):
        if has_process_instances(instance.process_def_id):
            raise ValidationError({"message": "当前流程已创建流程实例，不允许删除节点审核人规则"})

    def get_queryset(self):
        queryset = super().get_queryset()
        process_def_id = parse_optional_int_param(self.request.query_params.get("process_def_id"), "process_def_id")
        node_code = self.request.query_params.get("node_code")
        rule_type = self.request.query_params.get("rule_type")

        if "pk" not in getattr(self, "kwargs", {}):
            if process_def_id is None:
                raise ValidationError({"process_def_id": ["该参数必填"]})
            queryset = queryset.filter(process_def_id=process_def_id)
        if node_code:
            queryset = queryset.filter(node_code=node_code)
        if rule_type:
            queryset = queryset.filter(rule_type=rule_type)
        return queryset

    def attach_related_info(self, objects):
        rules = list(objects)
        if not rules:
            return rules

        node_map = build_node_name_map({item.process_def_id for item in rules if item.process_def_id is not None})

        for item in rules:
            item.node_name = node_map.get((item.process_def_id, item.node_code))
        return rules


class ProcessDefOptionView(APIView):
    """流程列表页筛选选项"""
    permission_classes = [IsAdminUserLevel]

    def get(self, request):
        data = {
            "status_options": choice_items(ProcessDefStatus.choices),
            "is_latest_options": boolean_choice_items(),
            "business_type_options": choice_items(ProcessBusinessType.choices),
        }
        return success_response(data)


class NodeDefOptionView(APIView):
    """节点配置辅助选项"""
    permission_classes = [IsAdminUserLevel]

    def get(self, request):
        data = {
            "node_type_options": choice_items(NodeType.choices),
            "join_strategy_options": choice_items(JoinStrategy.choices),
        }
        return success_response(data)


class TransitionDefOptionView(APIView):
    """流转配置辅助选项"""
    permission_classes = [IsAdminUserLevel]

    def get(self, request):
        data = {
            "action_code_options": choice_items(TransitionActionCode.choices),
            "condition_type_options": choice_items(ConditionType.choices),
        }
        return success_response(data)


class NodeAssigneeRuleOptionView(APIView):
    """节点审核规则配置辅助选项"""
    permission_classes = [IsAdminUserLevel]

    def get(self, request):
        data = {
            "rule_type_options": choice_items(AssigneeRuleType.choices),
        }
        return success_response(data)

class NodeAvailableActionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        process_def_id = parse_optional_int_param(
            request.query_params.get("process_def_id"),
            "process_def_id",
        )
        node_code = (request.query_params.get("node_code") or "").strip()

        if process_def_id is None:
            raise ValidationError({"process_def_id": ["该参数必填"]})
        if not node_code:
            raise ValidationError({"node_code": ["该参数必填"]})

        action_label_map = dict(TransitionActionCode.choices)
        action_codes = list(
            WfTransitionDef.objects.filter(
                process_def_id=process_def_id,
                from_node_code=node_code,
                is_enabled=True,
            )
            .order_by("priority", "id")
            .values_list("action_code", flat=True)
            .distinct()
        )
        data = [
            {
                "action_code": action_code,
                "action_name": action_label_map.get(action_code, action_code),
            }
            for action_code in action_codes
        ]
        return success_response(data)


class WfInstanceViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = WfInstance.objects.all().order_by("-id")
    serializer_class = WfInstanceSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            objects = self.attach_related_info(page)
            serializer = self.get_serializer(objects, many=True)
            return self.get_paginated_response(serializer.data)

        objects = self.attach_related_info(queryset)
        serializer = self.get_serializer(objects, many=True)
        return success_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        self.attach_related_info([instance])
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)

    def get_queryset(self):
        queryset = super().get_queryset()
        title = (self.request.query_params.get("title") or "").strip()
        status_value = (self.request.query_params.get("status") or "").strip()
        business_type = (self.request.query_params.get("business_type") or "").strip()
        applicant_id = parse_optional_int_param(self.request.query_params.get("applicant_id"), "applicant_id")

        if title:
            queryset = queryset.filter(title__icontains=title)
        if status_value:
            queryset = queryset.filter(status=status_value)
        if business_type:
            queryset = queryset.filter(business_type=business_type)
        if applicant_id is not None:
            queryset = queryset.filter(applicant_id=applicant_id)

        if self.request.user.user_level != User.Level.ADMIN:
            related_instance_ids = WfTask.objects.filter(assignee_id=self.request.user.id).values_list("instance_id", flat=True)
            queryset = queryset.filter(Q(applicant_id=self.request.user.id) | Q(id__in=related_instance_ids)).distinct()

        return queryset

    def attach_related_info(self, objects):
        instances = list(objects)
        if not instances:
            return instances

        instance_ids = [item.id for item in instances if item.id is not None]
        process_def_ids = {item.process_def_id for item in instances if item.process_def_id is not None}
        process_name_map = {
            item["id"]: item["process_name"]
            for item in WfProcessDef.objects.filter(id__in=process_def_ids).values("id", "process_name")
        }
        task_count_map = {
            item["instance_id"]: item["count"]
            for item in WfTask.objects.filter(instance_id__in=instance_ids)
            .values("instance_id")
            .annotate(count=Count("id"))
        }
        active_task_count_map = {
            item["instance_id"]: item["count"]
            for item in WfTask.objects.filter(
                instance_id__in=instance_ids,
                status__in=[TaskStatus.PENDING, TaskStatus.PROCESSING],
            )
            .values("instance_id")
            .annotate(count=Count("id"))
        }

        for item in instances:
            item.process_name = process_name_map.get(item.process_def_id)
            item.task_count = task_count_map.get(item.id, 0)
            item.active_task_count = active_task_count_map.get(item.id, 0)
        return instances

    @action(detail=True, methods=["post"], url_path="recall")
    def recall(self, request, *args, **kwargs):
        instance = self.get_object()
        service = WorkflowRuntimeService()
        instance = service.recall_instance(instance_id=instance.id, operator=request.user)
        self.attach_related_info([instance])
        return success_response(self.get_serializer(instance).data, message="流程撤回成功")


class WfTaskViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = WfTask.objects.all().order_by("-created_at", "-id")
    serializer_class = WfTaskSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            objects = self.attach_related_info(page)
            serializer = self.get_serializer(objects, many=True)
            return self.get_paginated_response(serializer.data)

        objects = self.attach_related_info(queryset)
        serializer = self.get_serializer(objects, many=True)
        return success_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        self.attach_related_info([instance])
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)

    def get_queryset(self):
        queryset = super().get_queryset()
        instance_id = parse_optional_int_param(self.request.query_params.get("instance_id"), "instance_id")
        status_value = (self.request.query_params.get("status") or "").strip()
        assignee_id = parse_optional_int_param(self.request.query_params.get("assignee_id"), "assignee_id")

        if instance_id is not None:
            queryset = queryset.filter(instance_id=instance_id)
        if status_value:
            queryset = queryset.filter(status=status_value)
        if assignee_id is not None:
            queryset = queryset.filter(assignee_id=assignee_id)

        if self.request.user.user_level != User.Level.ADMIN:
            applicant_instance_ids = WfInstance.objects.filter(applicant_id=self.request.user.id).values_list("id", flat=True)
            queryset = queryset.filter(Q(assignee_id=self.request.user.id) | Q(instance_id__in=applicant_instance_ids)).distinct()

        return queryset

    def attach_related_info(self, objects):
        tasks = list(objects)
        if not tasks:
            return tasks

        instance_ids = {item.instance_id for item in tasks if item.instance_id is not None}
        instance_map = {
            item["id"]: item
            for item in WfInstance.objects.filter(id__in=instance_ids).values("id", "title", "process_def_id")
        }
        org_ids = {
            parse_branch_org_id(item.branch_key)
            for item in tasks
            if parse_branch_org_id(item.branch_key) is not None
        }
        org_map = {
            item["id"]: item["org_name"]
            for item in OrgUnit.objects.filter(id__in=org_ids).values("id", "org_name")
        }

        for item in tasks:
            instance_info = instance_map.get(item.instance_id) or {}
            item.instance_title = instance_info.get("title")
            item.process_def_id = instance_info.get("process_def_id")
            item.branch_org_id = parse_branch_org_id(item.branch_key)
            item.branch_org_name = org_map.get(item.branch_org_id)
        return tasks

    @action(detail=True, methods=["post"], url_path="action")
    def handle_action(self, request, *args, **kwargs):
        task = self.get_object()
        serializer = WfTaskActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = WorkflowRuntimeService()
        service.handle_task_action(
            task_id=task.id,
            action_code=serializer.validated_data["action_code"],
            operator=request.user,
            comment=serializer.validated_data.get("comment"),
            selected_user_ids=serializer.validated_data.get("selected_user_ids"),
            target_branch_key=serializer.validated_data.get("target_branch_key"),
        )
        return success_response(None, message="任务处理成功")


class WfWorkItemViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = WfApprovalAssignment.objects.all()
    serializer_class = WfApprovalAssignmentSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.user_level == User.Level.ADMIN:
            return queryset
        return queryset.filter(assignee_id=self.request.user.id)

    def _filter_by_business_type(self, queryset):
        business_type = (self.request.query_params.get("business_type") or "").strip()
        if not business_type:
            return queryset

        instance_ids = WfInstance.objects.filter(business_type=business_type).values_list("id", flat=True)
        return queryset.filter(instance_id__in=instance_ids)

    def _get_todo_queryset(self):
        queryset = self.get_queryset().filter(handled_at__isnull=True)
        queryset = self._filter_by_business_type(queryset)
        return queryset.order_by("-received_at", "-id")

    def _get_done_queryset(self):
        queryset = (
            self.get_queryset()
            .filter(handled_at__isnull=False)
            .exclude(result=TaskResult.AUTO_SKIP)
        )
        queryset = self._filter_by_business_type(queryset)
        return queryset.order_by("-handled_at", "-id")

    def _attach_related_info(self, objects):
        assignments = list(objects)
        if not assignments:
            return assignments

        instance_ids = {item.instance_id for item in assignments if item.instance_id is not None}
        task_ids = {item.task_id for item in assignments if item.task_id is not None}

        instance_map = {
            item["id"]: item
            for item in WfInstance.objects.filter(id__in=instance_ids).values(
                "id",
                "title",
                "process_def_id",
                "business_type",
                "business_id",
                "status",
                "start_time",
                "end_time",
                "applicant_id",
                "applicant_name",
            )
        }
        process_def_ids = {
            item["process_def_id"]
            for item in instance_map.values()
            if item.get("process_def_id") is not None
        }
        process_name_map = {
            item["id"]: item["process_name"]
            for item in WfProcessDef.objects.filter(id__in=process_def_ids).values("id", "process_name")
        }
        task_map = {
            item["id"]: item
            for item in WfTask.objects.filter(id__in=task_ids).values("id", "status", "branch_key")
        }
        prop_status_sample_map = {}
        for item in ShenzhenPropStatus.objects.filter(process_instance_id__in=instance_ids).values(
            "process_instance_id",
            "cust_name",
            "ecif_cust_id",
            "accounting_org_id",
            "accounting_org_name",
        ).order_by("process_instance_id", "id"):
            prop_status_sample_map.setdefault(item["process_instance_id"], item)

        org_ids = {
            parse_branch_org_id(item["branch_key"])
            for item in task_map.values()
            if parse_branch_org_id(item.get("branch_key")) is not None
        }
        org_map = {
            item["id"]: item["org_name"]
            for item in OrgUnit.objects.filter(id__in=org_ids).values("id", "org_name")
        }

        for item in assignments:
            instance_info = instance_map.get(item.instance_id) or {}
            task_info = task_map.get(item.task_id) or {}
            prop_status_info = prop_status_sample_map.get(item.instance_id) or {}
            branch_key = task_info.get("branch_key")
            branch_org_id = parse_branch_org_id(branch_key)
            item.instance_title = instance_info.get("title")
            item.process_def_id = instance_info.get("process_def_id")
            item.process_name = process_name_map.get(item.process_def_id)
            item.business_type = instance_info.get("business_type")
            item.business_id = instance_info.get("business_id")
            item.instance_status = instance_info.get("status")
            item.start_time = instance_info.get("start_time")
            item.end_time = instance_info.get("end_time")
            item.applicant_id = instance_info.get("applicant_id")
            item.applicant_name = instance_info.get("applicant_name")
            item.task_status = task_info.get("status")
            item.branch_key = branch_key
            item.branch_org_id = branch_org_id
            item.branch_org_name = org_map.get(branch_org_id)
            item.cust_name = prop_status_info.get("cust_name")
            item.ecif_cust_id = prop_status_info.get("ecif_cust_id")
            item.accounting_org_id = prop_status_info.get("accounting_org_id")
            item.accounting_org_name = prop_status_info.get("accounting_org_name")
        return assignments

    def retrieve(self, request, *args, **kwargs):
        assignment = self.get_object()
        self._attach_related_info([assignment])
        serializer = self.get_serializer(assignment)
        prop_status_list = ShenzhenPropStatus.objects.filter(
            process_instance_id=assignment.instance_id
        ).order_by("id")
        return success_response(
            {
                **serializer.data,
                "prop_status_list": ShenzhenPropStatusSerializer(prop_status_list, many=True).data,
            }
        )

    @action(detail=False, methods=["get"], url_path="todo")
    def todo(self, request):
        queryset = self._get_todo_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            objects = self._attach_related_info(page)
            serializer = self.get_serializer(objects, many=True)
            return self.get_paginated_response(serializer.data)

        objects = self._attach_related_info(queryset)
        serializer = self.get_serializer(objects, many=True)
        return success_response(serializer.data)

    @action(detail=False, methods=["get"], url_path="done")
    def done(self, request):
        queryset = self._get_done_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            objects = self._attach_related_info(page)
            serializer = self.get_serializer(objects, many=True)
            return self.get_paginated_response(serializer.data)

        objects = self._attach_related_info(queryset)
        serializer = self.get_serializer(objects, many=True)
        return success_response(serializer.data)

    @action(detail=False, methods=["get"], url_path="reminder")
    def reminder(self, request):
        todo_count = self._get_todo_queryset().count()
        return success_response(
            {
                "has_todo": todo_count > 0,
                "todo_count": todo_count,
            }
        )


class WfTaskLogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = WfTaskLog.objects.all().order_by("id")
    serializer_class = WfTaskLogSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)

    def get_queryset(self):
        queryset = super().get_queryset()
        instance_id = parse_optional_int_param(self.request.query_params.get("instance_id"), "instance_id")
        task_id = parse_optional_int_param(self.request.query_params.get("task_id"), "task_id")
        if instance_id is not None:
            queryset = queryset.filter(instance_id=instance_id)
        if task_id is not None:
            queryset = queryset.filter(task_id=task_id)

        if self.request.user.user_level != User.Level.ADMIN:
            applicant_instance_ids = WfInstance.objects.filter(applicant_id=self.request.user.id).values_list("id", flat=True)
            assignee_instance_ids = WfTask.objects.filter(assignee_id=self.request.user.id).values_list("instance_id", flat=True)
            queryset = queryset.filter(Q(instance_id__in=applicant_instance_ids) | Q(instance_id__in=assignee_instance_ids)).distinct()
        return queryset
