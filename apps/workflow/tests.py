from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from rest_framework import serializers as drf_serializers
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.organization.models import UserOrgRelation
from apps.users.models import User
from apps.workflow.runtime import WorkflowRuntimeService
from apps.workflow.serializers import WfInstanceSerializer, WfNodeDefSerializer, WfProcessDefSerializer
from apps.workflow.views import (
    NodeAssigneeRuleOptionView,
    NodeDefOptionView,
    ProcessDefOptionView,
    TransitionDefOptionView,
    WfNodeAssigneeRuleViewSet,
    WfNodeDefViewSet,
    WfProcessDefViewSet,
    WfTaskLogViewSet,
    WfTransitionDefViewSet,
    WfTaskViewSet,
    WfWorkItemViewSet,
)


class WorkflowViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.admin_user = SimpleNamespace(is_authenticated=True, user_level=User.Level.ADMIN)

    def test_process_def_option_view_returns_flat_options(self):
        request = self.factory.get("/api/workflow/process-def-options/")
        force_authenticate(request, user=self.admin_user)

        response = ProcessDefOptionView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn("status_options", response.data["data"])
        self.assertIn("is_latest_options", response.data["data"])
        self.assertEqual(
            response.data["data"]["business_type_options"],
            [
                {"value": "report_submit", "label": "报表"},
                {"value": "performance_claim", "label": "业绩认领"},
                {"value": "performance_transfer", "label": "业绩移交"},
            ],
        )

    def test_node_def_option_view_returns_global_options(self):
        request = self.factory.get("/api/workflow/node-def-options/")
        force_authenticate(request, user=self.admin_user)

        response = NodeDefOptionView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn("node_type_options", response.data["data"])
        self.assertIn("join_strategy_options", response.data["data"])
        self.assertEqual(
            response.data["data"]["node_type_options"],
            [
                {"value": "start", "label": "开始节点"},
                {"value": "manual", "label": "人工审核节点"},
                {"value": "auto", "label": "自动处理节点"},
                {"value": "end", "label": "结束节点"},
            ],
        )

    def test_transition_def_option_view_returns_global_options(self):
        request = self.factory.get("/api/workflow/transition-def-options/")
        force_authenticate(request, user=self.admin_user)

        response = TransitionDefOptionView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn("action_code_options", response.data["data"])
        self.assertIn("condition_type_options", response.data["data"])
        self.assertEqual(
            response.data["data"]["condition_type_options"],
            [
                {"value": "none", "label": "无条件"},
                {"value": "script", "label": "脚本"},
            ],
        )

    def test_node_assignee_rule_option_view_returns_global_options(self):
        request = self.factory.get("/api/workflow/node-assignee-rule-options/")
        force_authenticate(request, user=self.admin_user)

        response = NodeAssigneeRuleOptionView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn("rule_type_options", response.data["data"])

    def test_process_def_viewset_applies_query_filters(self):
        request = self.factory.get(
            "/api/workflow/process-defs/",
            {"process_code": "EXP", "business_type": "report_submit", "status": "active", "is_latest": "true"},
        )
        view = WfProcessDefViewSet()
        view.request = Request(request)

        queryset = MagicMock()
        queryset.filter.return_value = queryset
        with patch.object(WfProcessDefViewSet, "queryset", queryset):
            result = view.get_queryset()

        self.assertIs(result, queryset)
        queryset.filter.assert_any_call(process_code__icontains="EXP")
        queryset.filter.assert_any_call(business_type="report_submit")
        queryset.filter.assert_any_call(status="active")
        queryset.filter.assert_any_call(is_latest=True)

    def test_node_def_list_requires_process_def_id(self):
        request = self.factory.get("/api/workflow/node-defs/")
        view = WfNodeDefViewSet()
        view.request = Request(request)
        view.kwargs = {}

        with patch.object(WfNodeDefViewSet, "queryset", MagicMock()):
            with self.assertRaises(ValidationError) as ctx:
                view.get_queryset()

        self.assertIn("process_def_id", ctx.exception.detail)

    def test_node_def_viewset_applies_process_scoped_filters(self):
        request = self.factory.get("/api/workflow/node-defs/", {"process_def_id": "12", "join_strategy": "all_pass"})
        view = WfNodeDefViewSet()
        view.request = Request(request)
        view.kwargs = {}

        queryset = MagicMock()
        queryset.filter.return_value = queryset
        with patch.object(WfNodeDefViewSet, "queryset", queryset):
            result = view.get_queryset()

        self.assertIs(result, queryset)
        queryset.filter.assert_any_call(process_def_id=12)
        queryset.filter.assert_any_call(join_strategy="all_pass")

    def test_transition_def_list_requires_process_def_id(self):
        request = self.factory.get("/api/workflow/transition-defs/")
        view = WfTransitionDefViewSet()
        view.request = Request(request)
        view.kwargs = {}

        with patch.object(WfTransitionDefViewSet, "queryset", MagicMock()):
            with self.assertRaises(ValidationError) as ctx:
                view.get_queryset()

        self.assertIn("process_def_id", ctx.exception.detail)

    def test_transition_def_viewset_applies_condition_type_filter(self):
        request = self.factory.get("/api/workflow/transition-defs/", {"process_def_id": "12", "condition_type": "script"})
        view = WfTransitionDefViewSet()
        view.request = Request(request)
        view.kwargs = {}

        queryset = MagicMock()
        queryset.filter.return_value = queryset
        with patch.object(WfTransitionDefViewSet, "queryset", queryset):
            result = view.get_queryset()

        self.assertIs(result, queryset)
        queryset.filter.assert_any_call(process_def_id=12)
        queryset.filter.assert_any_call(condition_type="script")

    def test_assignee_rule_list_requires_process_def_id(self):
        request = self.factory.get("/api/workflow/node-assignee-rules/")
        view = WfNodeAssigneeRuleViewSet()
        view.request = Request(request)
        view.kwargs = {}

        with patch.object(WfNodeAssigneeRuleViewSet, "queryset", MagicMock()):
            with self.assertRaises(ValidationError) as ctx:
                view.get_queryset()

        self.assertIn("process_def_id", ctx.exception.detail)

    def test_assignee_rule_viewset_applies_filters(self):
        request = self.factory.get("/api/workflow/node-assignee-rules/", {"process_def_id": "12", "rule_type": "role"})
        view = WfNodeAssigneeRuleViewSet()
        view.request = Request(request)
        view.kwargs = {}

        queryset = MagicMock()
        queryset.filter.return_value = queryset
        with patch.object(WfNodeAssigneeRuleViewSet, "queryset", queryset):
            result = view.get_queryset()

        self.assertIs(result, queryset)
        queryset.filter.assert_any_call(process_def_id=12)
        queryset.filter.assert_any_call(rule_type="role")

    @patch("apps.workflow.views.WfTransitionDef.objects.filter")
    @patch("apps.workflow.views.WfNodeAssigneeRule.objects.filter")
    @patch("apps.workflow.views.WfNodeDef.objects.filter")
    @patch("apps.workflow.views.WfInstance.objects.filter")
    def test_process_def_destroy_blocks_when_related_records_exist(
        self,
        mock_instance_filter,
        mock_node_filter,
        mock_rule_filter,
        mock_transition_filter,
    ):
        mock_instance_filter.return_value.exists.return_value = False
        mock_node_filter.return_value.count.return_value = 2
        mock_rule_filter.return_value.count.return_value = 1
        mock_transition_filter.return_value.count.return_value = 0

        request = self.factory.delete("/api/workflow/process-defs/1/")
        view = WfProcessDefViewSet()
        view.request = Request(request)
        view.kwargs = {}
        view.format_kwarg = None
        view.action_map = {}
        view.get_object = MagicMock(return_value=SimpleNamespace(id=1))

        with self.assertRaises(ValidationError) as ctx:
            view.destroy(request)

        self.assertIn("当前流程定义仍关联节点定义 2 条, 节点审核员规则 1 条", str(ctx.exception.detail))

    @patch("apps.workflow.views.WfInstance.objects.filter")
    def test_process_def_destroy_blocks_when_instances_exist(self, mock_instance_filter):
        mock_instance_filter.return_value.exists.return_value = True

        request = self.factory.delete("/api/workflow/process-defs/1/")
        view = WfProcessDefViewSet()
        view.request = Request(request)
        view.kwargs = {}
        view.format_kwarg = None
        view.action_map = {}
        view.get_object = MagicMock(return_value=SimpleNamespace(id=1))

        with self.assertRaises(ValidationError) as ctx:
            view.destroy(request)

        self.assertIn("当前流程定义已创建流程实例，不允许删除", str(ctx.exception.detail))

    @patch.object(drf_serializers.ModelSerializer, "update")
    @patch("apps.workflow.serializers.transaction.atomic")
    @patch("apps.workflow.serializers.WfTransitionDef.objects.filter")
    @patch("apps.workflow.serializers.WfNodeAssigneeRule.objects.filter")
    def test_node_serializer_updates_related_rules_and_transitions_when_code_changes(
        self,
        mock_rule_filter,
        mock_transition_filter,
        _mock_atomic,
        mock_super_update,
    ):
        instance = SimpleNamespace(process_def_id=1, node_code="node_a")
        serializer = WfNodeDefSerializer()
        mock_super_update.return_value = instance

        rule_queryset = MagicMock()
        from_transition_queryset = MagicMock()
        to_transition_queryset = MagicMock()
        mock_rule_filter.return_value = rule_queryset
        mock_transition_filter.side_effect = [from_transition_queryset, to_transition_queryset]

        serializer.update(instance, {"node_code": "node_b"})

        mock_rule_filter.assert_called_once_with(process_def_id=1, node_code="node_a")
        rule_queryset.update.assert_called_once_with(node_code="node_b")
        from_transition_queryset.update.assert_called_once_with(from_node_code="node_b")
        to_transition_queryset.update.assert_called_once_with(to_node_code="node_b")

    @patch("apps.workflow.views.WfInstance.objects.filter")
    def test_node_update_blocks_when_instances_exist(self, mock_instance_filter):
        mock_instance_filter.return_value.exists.return_value = True

        view = WfNodeDefViewSet()
        view.get_object = MagicMock(return_value=SimpleNamespace(id=1, process_def_id=10))

        with self.assertRaises(ValidationError) as ctx:
            view.validate_update_allowed(view.get_object())

        self.assertIn("当前流程已创建流程实例，不允许修改节点定义", str(ctx.exception.detail))

    @patch("apps.workflow.views.WfInstance.objects.filter")
    def test_transition_update_blocks_when_instances_exist(self, mock_instance_filter):
        mock_instance_filter.return_value.exists.return_value = True

        view = WfTransitionDefViewSet()
        view.get_object = MagicMock(return_value=SimpleNamespace(id=1, process_def_id=10))

        with self.assertRaises(ValidationError) as ctx:
            view.validate_update_allowed(view.get_object())

        self.assertIn("当前流程已创建流程实例，不允许修改流转定义", str(ctx.exception.detail))

    @patch("apps.workflow.views.WfInstance.objects.filter")
    def test_assignee_rule_destroy_blocks_when_instances_exist(self, mock_instance_filter):
        mock_instance_filter.return_value.exists.return_value = True

        request = self.factory.delete("/api/workflow/node-assignee-rules/1/")
        view = WfNodeAssigneeRuleViewSet()
        view.request = Request(request)
        view.kwargs = {}
        view.format_kwarg = None
        view.action_map = {}
        view.get_object = MagicMock(return_value=SimpleNamespace(id=1, process_def_id=10))

        with self.assertRaises(ValidationError) as ctx:
            view.destroy(request)

        self.assertIn("当前流程已创建流程实例，不允许删除节点审核人规则", str(ctx.exception.detail))

    @patch("apps.workflow.serializers.WfProcessDef.objects.filter")
    def test_process_serializer_auto_increments_version_when_missing(self, mock_process_filter):
        max_version_queryset = MagicMock()
        max_version_queryset.aggregate.return_value = {"max_version": 3}
        duplicate_queryset = MagicMock()
        duplicate_queryset.exists.return_value = False
        mock_process_filter.side_effect = [max_version_queryset, duplicate_queryset]

        serializer = WfProcessDefSerializer(
            data={
                "process_code": "new_proc",
                "process_name": "新流程",
                "business_type": "report_submit",
                "status": "draft",
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["version"], 4)

    @patch("apps.workflow.views.transaction.atomic")
    @patch("apps.workflow.views.WfTransitionDef.objects.bulk_create")
    @patch("apps.workflow.views.WfNodeAssigneeRule.objects.bulk_create")
    @patch("apps.workflow.views.WfNodeDef.objects.bulk_create")
    @patch("apps.workflow.views.WfTransitionDef.objects.filter")
    @patch("apps.workflow.views.WfNodeAssigneeRule.objects.filter")
    @patch("apps.workflow.views.WfNodeDef.objects.filter")
    @patch("apps.workflow.views.WfProcessDef.objects.filter")
    @patch("apps.workflow.views.WfProcessDef.objects.create")
    def test_process_copy_creates_new_process_and_related_records(
        self,
        mock_process_create,
        mock_process_filter,
        mock_node_filter,
        mock_rule_filter,
        mock_transition_filter,
        mock_node_bulk_create,
        mock_rule_bulk_create,
        mock_transition_bulk_create,
        _mock_atomic,
    ):
        source_process_def = SimpleNamespace(
            id=1,
            process_code="source_proc",
            process_name="源流程",
            business_type="report_submit",
            status="active",
            remark="源备注",
        )
        target_process_def = SimpleNamespace(
            id=2,
            process_code="source_proc",
            process_name="源流程",
            business_type="report_submit",
            version=4,
            status="active",
            is_latest=True,
            remark="源备注",
            created_at=None,
            updated_at=None,
        )
        mock_process_create.return_value = target_process_def

        max_version_queryset = MagicMock()
        max_version_queryset.aggregate.return_value = {"max_version": 3}
        latest_queryset = MagicMock()
        latest_exclude_queryset = MagicMock()
        latest_queryset.exclude.return_value = latest_exclude_queryset
        mock_process_filter.side_effect = [max_version_queryset, latest_queryset]

        source_nodes = [
            SimpleNamespace(
                node_code="start",
                node_name="开始",
                node_type="start",
                auto_func_name=None,
                node_order=10,
                is_parallel=False,
                parallel_mode=None,
                join_strategy=None,
                can_reject=False,
                can_return=False,
                auto_create_task=True,
                remark="节点备注",
            )
        ]
        source_rules = [
            SimpleNamespace(
                node_code="start",
                rule_type="applicant",
                rule_value="",
                remark="规则备注",
            )
        ]
        source_transitions = [
            SimpleNamespace(
                from_node_code="start",
                to_node_code="end",
                action_code="submit",
                condition_type="none",
                condition_expr=None,
                priority=10,
                is_enabled=True,
                remark="流转备注",
            )
        ]

        node_queryset = MagicMock()
        node_queryset.order_by.return_value = source_nodes
        mock_node_filter.return_value = node_queryset

        rule_queryset = MagicMock()
        rule_queryset.order_by.return_value = source_rules
        mock_rule_filter.return_value = rule_queryset

        transition_queryset = MagicMock()
        transition_queryset.order_by.return_value = source_transitions
        mock_transition_filter.return_value = transition_queryset

        request = SimpleNamespace(
            data={},
            query_params={},
        )

        view = WfProcessDefViewSet()
        view.request = request
        view.kwargs = {"pk": "1"}
        view.action = "copy"
        view.format_kwarg = None
        view.get_object = MagicMock(return_value=source_process_def)

        with patch.object(WfProcessDefViewSet, "attach_related_info", return_value=[target_process_def]):
            response = view.copy(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["message"], "复制成功")
        self.assertEqual(response.data["data"]["source_process_def_id"], 1)
        self.assertEqual(response.data["data"]["copied_counts"]["node_count"], 1)
        self.assertEqual(response.data["data"]["copied_counts"]["assignee_rule_count"], 1)
        self.assertEqual(response.data["data"]["copied_counts"]["transition_count"], 1)
        mock_process_create.assert_called_once_with(
            process_code="source_proc",
            process_name="源流程",
            business_type="report_submit",
            version=4,
            status="active",
            is_latest=True,
            remark="源备注",
        )
        latest_queryset.exclude.assert_called_once_with(id=2)
        latest_exclude_queryset.update.assert_called_once_with(is_latest=False)

        created_nodes = mock_node_bulk_create.call_args.args[0]
        self.assertEqual(len(created_nodes), 1)
        self.assertEqual(created_nodes[0].process_def_id, 2)
        self.assertEqual(created_nodes[0].node_code, "start")
        self.assertEqual(created_nodes[0].node_type, "start")

        created_rules = mock_rule_bulk_create.call_args.args[0]
        self.assertEqual(len(created_rules), 1)
        self.assertEqual(created_rules[0].process_def_id, 2)
        self.assertEqual(created_rules[0].node_code, "start")

        created_transitions = mock_transition_bulk_create.call_args.args[0]
        self.assertEqual(len(created_transitions), 1)
        self.assertEqual(created_transitions[0].process_def_id, 2)
        self.assertEqual(created_transitions[0].from_node_code, "start")

    def test_runtime_service_report_parallel_split_blocks_duplicate_org(self):
        service = WorkflowRuntimeService()
        with patch.object(
            service,
            "_collect_selected_user_orgs",
            side_effect=ValidationError({"message": "所选用户存在相同机构，请重新选择，保证一个机构只对应一个并行分支"}),
        ):
            with self.assertRaises(ValidationError) as ctx:
                service.report_parallel_split(
                    instance=SimpleNamespace(id=1),
                    node=SimpleNamespace(node_code="parallel_check"),
                    source_task=None,
                    context={"selected_user_ids": [1, 2]},
                )

        self.assertIn("相同机构", str(ctx.exception.detail))

    def test_runtime_service_claim_parallel_merge_check_returns_multiple_branch_context(self):
        service = WorkflowRuntimeService()
        with patch.object(service, "_count_parallel_branches", return_value=3):
            result = service.claim_parallel_merge_check(
                instance=SimpleNamespace(id=99),
                node=SimpleNamespace(node_code="merge"),
                source_task=SimpleNamespace(parallel_group="group_1"),
                context={},
            )

        self.assertEqual(
            result["context"],
            {
                "branch_count": 3,
                "has_multiple_branches": True,
                "parallel_group": "group_1",
            },
        )
        self.assertEqual(result["target_node_code"], "perf_claim_operator_assign")

    def test_runtime_service_claim_parallel_merge_check_returns_end_for_single_branch(self):
        service = WorkflowRuntimeService()
        with patch.object(service, "_count_parallel_branches", return_value=1):
            result = service.claim_parallel_merge_check(
                instance=SimpleNamespace(id=99),
                node=SimpleNamespace(node_code="merge"),
                source_task=SimpleNamespace(parallel_group="group_1"),
                context={},
            )

        self.assertEqual(result["target_node_code"], "perf_claim_end")

    @patch("apps.workflow.runtime.WfTask.objects.filter")
    def test_runtime_service_parallel_sibling_check_uses_parallel_group_scope(self, mock_task_filter):
        service = WorkflowRuntimeService()
        task_queryset = MagicMock()
        sibling_queryset = MagicMock()
        task_queryset.exclude.return_value = sibling_queryset
        sibling_queryset.exists.return_value = True
        mock_task_filter.return_value = task_queryset

        result = service._has_pending_parallel_sibling(
            SimpleNamespace(
                id=10,
                instance_id=99,
                node_code="branch_review",
                branch_key="org_1001",
                parallel_group="group_1",
            )
        )

        self.assertTrue(result)
        mock_task_filter.assert_called_once_with(
            instance_id=99,
            parallel_group="group_1",
            status__in=["pending", "processing"],
        )
        task_queryset.exclude.assert_called_once_with(branch_key="org_1001")

    def test_runtime_service_validate_single_rule_user_rejects_multi_user_value(self):
        service = WorkflowRuntimeService()
        rule = SimpleNamespace(rule_value="10,20")
        node = SimpleNamespace(node_name="固定审批人")

        with self.assertRaises(ValidationError) as ctx:
            service._validate_single_rule_user(rule, node, required=True)

        self.assertIn("多个审批人", str(ctx.exception.detail))

    def test_instance_serializer_returns_counts_only(self):
        instance = SimpleNamespace(
            id=101,
            title="业绩认领单",
            process_def_id=11,
            process_name="业绩认领流程",
            business_type="performance_claim",
            business_id=501,
            applicant_id=1,
            applicant_name="发起人",
            current_node_code="branch_review",
            current_node_name="分行审核",
            status="running",
            get_status_display=lambda: "进行中",
            task_count=3,
            active_task_count=1,
            start_time=None,
            end_time=None,
            created_at=None,
            updated_at=None,
        )

        data = WfInstanceSerializer(instance).data

        self.assertEqual(data["task_count"], 3)
        self.assertEqual(data["active_task_count"], 1)
        self.assertNotIn("tasks", data)
        self.assertNotIn("instance_logs", data)

    @patch.object(WorkflowRuntimeService, "handle_task_action")
    def test_task_handle_action_returns_success_without_instance_payload(self, mock_handle_task_action):
        mock_handle_task_action.return_value = SimpleNamespace(id=101)
        request = SimpleNamespace(
            data={"action_code": "approve"},
            user=self.admin_user,
        )

        view = WfTaskViewSet()
        view.request = request
        view.kwargs = {}
        view.get_object = MagicMock(return_value=SimpleNamespace(id=1))

        response = view.handle_action(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "任务处理成功")
        self.assertIsNone(response.data["data"])

    def test_work_item_viewset_builds_todo_queryset_for_current_user(self):
        request = self.factory.get("/api/workflow/work-items/todo/")
        view = WfWorkItemViewSet()
        view.request = Request(request)
        view.request.user = SimpleNamespace(id=7, user_level=User.Level.NORMAL)

        base_queryset = MagicMock()
        user_queryset = MagicMock()
        filtered_queryset = MagicMock()
        ordered_queryset = MagicMock()
        base_queryset.filter.return_value = user_queryset
        user_queryset.filter.return_value = filtered_queryset
        filtered_queryset.order_by.return_value = ordered_queryset

        with patch.object(WfWorkItemViewSet, "queryset", base_queryset):
            result = view._get_todo_queryset()

        self.assertIs(result, ordered_queryset)
        base_queryset.filter.assert_called_once_with(assignee_id=7)
        user_queryset.filter.assert_called_once_with(handled_at__isnull=True)
        filtered_queryset.order_by.assert_called_once_with("-received_at", "-id")

    @patch("apps.workflow.views.WfInstance.objects.filter")
    def test_work_item_viewset_filters_todo_queryset_by_business_type(self, mock_instance_filter):
        request = self.factory.get("/api/workflow/work-items/todo/", {"business_type": "performance_claim"})
        view = WfWorkItemViewSet()
        view.request = Request(request)
        view.request.user = SimpleNamespace(id=7)

        base_queryset = MagicMock()
        handled_queryset = MagicMock()
        filtered_business_queryset = MagicMock()
        ordered_queryset = MagicMock()
        view.get_queryset = MagicMock(return_value=base_queryset)
        base_queryset.filter.return_value = handled_queryset
        handled_queryset.filter.return_value = filtered_business_queryset
        filtered_business_queryset.order_by.return_value = ordered_queryset
        mock_instance_filter.return_value.values_list.return_value = [101, 102]

        result = view._get_todo_queryset()

        self.assertIs(result, ordered_queryset)
        mock_instance_filter.assert_called_once_with(business_type="performance_claim")
        handled_queryset.filter.assert_called_once_with(instance_id__in=[101, 102])
        filtered_business_queryset.order_by.assert_called_once_with("-received_at", "-id")

    def test_work_item_viewset_builds_done_queryset_for_current_user(self):
        request = self.factory.get("/api/workflow/work-items/done/")
        view = WfWorkItemViewSet()
        view.request = Request(request)
        view.request.user = SimpleNamespace(id=9, user_level=User.Level.NORMAL)

        base_queryset = MagicMock()
        user_queryset = MagicMock()
        handled_queryset = MagicMock()
        exclude_queryset = MagicMock()
        ordered_queryset = MagicMock()
        base_queryset.filter.return_value = user_queryset
        user_queryset.filter.return_value = handled_queryset
        handled_queryset.exclude.return_value = exclude_queryset
        exclude_queryset.order_by.return_value = ordered_queryset

        with patch.object(WfWorkItemViewSet, "queryset", base_queryset):
            result = view._get_done_queryset()

        self.assertIs(result, ordered_queryset)
        base_queryset.filter.assert_called_once_with(assignee_id=9)
        user_queryset.filter.assert_called_once_with(handled_at__isnull=False)
        handled_queryset.exclude.assert_called_once_with(result="auto_skip")
        exclude_queryset.order_by.assert_called_once_with("-handled_at", "-id")

    @patch("apps.workflow.views.WfInstance.objects.filter")
    def test_work_item_viewset_filters_done_queryset_by_business_type(self, mock_instance_filter):
        request = self.factory.get("/api/workflow/work-items/done/", {"business_type": "performance_transfer"})
        view = WfWorkItemViewSet()
        view.request = Request(request)
        view.request.user = SimpleNamespace(id=9)

        base_queryset = MagicMock()
        handled_queryset = MagicMock()
        excluded_queryset = MagicMock()
        filtered_business_queryset = MagicMock()
        ordered_queryset = MagicMock()
        view.get_queryset = MagicMock(return_value=base_queryset)
        base_queryset.filter.return_value = handled_queryset
        handled_queryset.exclude.return_value = excluded_queryset
        excluded_queryset.filter.return_value = filtered_business_queryset
        filtered_business_queryset.order_by.return_value = ordered_queryset
        mock_instance_filter.return_value.values_list.return_value = [201]

        result = view._get_done_queryset()

        self.assertIs(result, ordered_queryset)
        mock_instance_filter.assert_called_once_with(business_type="performance_transfer")
        excluded_queryset.filter.assert_called_once_with(instance_id__in=[201])
        filtered_business_queryset.order_by.assert_called_once_with("-handled_at", "-id")

    def test_work_item_viewset_reminder_returns_todo_count(self):
        request = self.factory.get("/api/workflow/work-items/reminder/")
        view = WfWorkItemViewSet()
        view.request = Request(request)

        todo_queryset = MagicMock()
        todo_queryset.count.return_value = 2
        view._get_todo_queryset = MagicMock(return_value=todo_queryset)

        response = view.reminder(view.request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"], {"has_todo": True, "todo_count": 2})

    @patch("apps.workflow.views.OrgUnit.objects.filter")
    @patch("apps.workflow.views.ShenzhenPropStatus.objects.filter")
    @patch("apps.workflow.views.WfTask.objects.filter")
    @patch("apps.workflow.views.WfProcessDef.objects.filter")
    @patch("apps.workflow.views.WfInstance.objects.filter")
    def test_work_item_attach_related_info_includes_instance_and_prop_status_fields(
        self,
        mock_instance_filter,
        mock_process_def_filter,
        mock_task_filter,
        mock_prop_status_filter,
        mock_org_filter,
    ):
        request = self.factory.get("/api/workflow/work-items/todo/")
        view = WfWorkItemViewSet()
        view.request = Request(request)
        view.request.user = SimpleNamespace(id=7, user_level=User.Level.NORMAL)

        mock_instance_filter.return_value.values.return_value = [
            {
                "id": 101,
                "title": "业绩认领流程",
                "process_def_id": 11,
                "business_type": "performance_claim",
                "business_id": 501,
                "status": "running",
                "start_time": "2026-04-30T10:00:00",
                "end_time": None,
                "applicant_id": 1,
                "applicant_name": "发起人",
            }
        ]
        mock_process_def_filter.return_value.values.return_value = [{"id": 11, "process_name": "业绩认领审批"}]
        mock_task_filter.return_value.values.return_value = [{"id": 301, "status": "pending", "branch_key": "org_88"}]
        mock_prop_status_filter.return_value.values.return_value.order_by.return_value = [
            {"process_instance_id": 101, "cust_name": "客户A", "ecif_cust_id": "C001"}
        ]
        mock_org_filter.return_value.values.return_value = [{"id": 88, "org_name": "深圳分行"}]

        assignment = SimpleNamespace(instance_id=101, task_id=301)

        result = view._attach_related_info([assignment])

        self.assertEqual(result[0].instance_title, "业绩认领流程")
        self.assertEqual(result[0].process_name, "业绩认领审批")
        self.assertEqual(result[0].business_type, "performance_claim")
        self.assertEqual(result[0].instance_status, "running")
        self.assertEqual(result[0].applicant_name, "发起人")
        self.assertEqual(result[0].branch_org_name, "深圳分行")
        self.assertEqual(result[0].cust_name, "客户A")
        self.assertEqual(result[0].ecif_cust_id, "C001")

    @patch("apps.workflow.views.ShenzhenPropStatusSerializer")
    @patch("apps.workflow.views.ShenzhenPropStatus.objects.filter")
    def test_work_item_retrieve_returns_bound_prop_status_list(self, mock_prop_status_filter, mock_prop_status_serializer):
        request = self.factory.get("/api/workflow/work-items/1/")
        view = WfWorkItemViewSet()
        view.request = Request(request)
        view.request.user = SimpleNamespace(id=7, user_level=User.Level.NORMAL)
        view.get_object = MagicMock(return_value=SimpleNamespace(id=1, instance_id=101, task_id=301))
        view.get_serializer = MagicMock(return_value=SimpleNamespace(data={"id": 1, "instance_id": 101, "task_id": 301}))
        view._attach_related_info = MagicMock()

        prop_status_queryset = MagicMock()
        mock_prop_status_filter.return_value = prop_status_queryset
        prop_status_queryset.order_by.return_value = ["row1", "row2"]
        mock_prop_status_serializer.return_value.data = [{"id": 11}, {"id": 12}]

        response = view.retrieve(view.request, pk=1)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["instance_id"], 101)
        self.assertEqual(response.data["data"]["prop_status_list"], [{"id": 11}, {"id": 12}])
        view._attach_related_info.assert_called_once()
        mock_prop_status_filter.assert_called_once_with(process_instance_id=101)

    def test_task_log_viewset_applies_instance_and_task_filters(self):
        request = self.factory.get("/api/workflow/task-logs/", {"instance_id": "12", "task_id": "34"})
        view = WfTaskLogViewSet()
        view.request = Request(request)
        view.request.user = self.admin_user

        queryset = MagicMock()
        queryset.filter.return_value = queryset
        with patch.object(WfTaskLogViewSet, "queryset", queryset):
            result = view.get_queryset()

        self.assertIs(result, queryset)
        queryset.filter.assert_any_call(instance_id=12)
        queryset.filter.assert_any_call(task_id=34)

    @patch.object(WorkflowRuntimeService, "_enter_manual_node")
    @patch.object(WorkflowRuntimeService, "_write_log")
    @patch.object(WorkflowRuntimeService, "_close_tasks")
    @patch.object(WorkflowRuntimeService, "_get_first_manual_node_codes_after_start", return_value=["branch_review"])
    @patch.object(WorkflowRuntimeService, "_get_start_node")
    @patch.object(WorkflowRuntimeService, "_get_node")
    @patch("apps.workflow.runtime.WfTask.objects.filter")
    @patch("apps.workflow.runtime.WfInstance.objects.filter")
    def test_runtime_service_recall_instance_returns_to_start_node(
        self,
        mock_instance_filter,
        mock_task_filter,
        mock_get_node,
        mock_get_start_node,
        _mock_first_manual_nodes,
        mock_close_tasks,
        mock_write_log,
        mock_enter_manual_node,
    ):
        service = WorkflowRuntimeService()
        instance = SimpleNamespace(
            id=101,
            process_def_id=11,
            applicant_id=1,
            current_node_code="branch_review",
            current_node_name="分行审核",
            status="running",
            end_time=None,
        )
        applicant = SimpleNamespace(id=1, full_name="发起人")
        start_node = SimpleNamespace(node_code="start", node_name="开始节点")
        current_node = SimpleNamespace(node_code="branch_review", node_name="分行审核")
        open_task = SimpleNamespace(id=301, node_code="branch_review", branch_key=None, parallel_group=None)

        instance_get_queryset = MagicMock()
        instance_get_queryset.first.return_value = instance
        instance_update_queryset = MagicMock()
        mock_instance_filter.side_effect = [instance_get_queryset, instance_update_queryset]

        task_queryset = MagicMock()
        task_queryset.order_by.return_value = [open_task]
        mock_task_filter.return_value = task_queryset

        mock_get_start_node.return_value = start_node
        mock_get_node.return_value = current_node

        result = WorkflowRuntimeService.recall_instance.__wrapped__(service, instance_id=101, operator=applicant)

        self.assertIs(result, instance)
        mock_task_filter.assert_called_once_with(instance_id=101, status__in=["pending", "processing"])
        mock_close_tasks.assert_called_once()
        instance_update_queryset.update.assert_called_once()
        mock_write_log.assert_called_once()
        mock_enter_manual_node.assert_called_once()
        self.assertEqual(instance.current_node_code, "start")
        self.assertEqual(instance.current_node_name, "开始节点")


class WorkflowRuntimeTests(SimpleTestCase):
    def test_validate_task_action_rejects_unconfigured_action_and_lists_allowed_actions(self):
        service = WorkflowRuntimeService()
        node = SimpleNamespace(process_def_id=11, node_code="branch_review", node_name="分行审核", can_reject=True, can_return=True)
        task = SimpleNamespace(parallel_group=None, branch_key=None)

        with patch.object(service, "_get_start_node", return_value=SimpleNamespace(node_code="start")), patch.object(
            service,
            "_get_node_allowed_action_codes",
            return_value=["approve", "return"],
        ):
            with self.assertRaises(ValidationError) as ctx:
                service._validate_task_action(
                    node=node,
                    action_code="reject",
                    selected_user_ids=None,
                    target_branch_key=None,
                    task=task,
                )

        self.assertEqual(
            ctx.exception.detail["message"],
            "节点[分行审核]不允许执行动作[reject]，当前只能使用：审批通过(approve)、退回(return)",
        )

    @patch("apps.workflow.runtime.User.objects.filter")
    @patch("apps.workflow.runtime.UserOrgRelation.objects.filter")
    def test_resolve_node_assignee_uses_source_task_org_when_branch_key_invalid(
        self,
        mock_relation_filter,
        mock_user_filter,
    ):
        service = WorkflowRuntimeService()
        instance = SimpleNamespace(id=101, process_def_id=11, applicant_id=1)
        node = SimpleNamespace(node_code="branch_review", node_name="分行审核")
        rule = SimpleNamespace(rule_type="employee_level", rule_value="L1")
        relation = SimpleNamespace(user_id=9, org_id=88)
        approver = SimpleNamespace(id=9, full_name="审核人")

        relation_queryset = MagicMock()
        relation_queryset.order_by.return_value = [relation]
        mock_relation_filter.return_value = relation_queryset
        mock_user_filter.return_value = [approver]

        with patch.object(service, "_get_rule", return_value=rule), patch.object(
            service,
            "_resolve_org_id_from_source_task",
            return_value=88,
        ) as mock_resolve_org, patch.object(service, "_get_user_primary_relation") as mock_applicant_relation:
            assignee = service._resolve_node_assignee(
                instance=instance,
                node=node,
                branch_key="bad_branch_key",
                source_task=SimpleNamespace(id=301, assignee_id=3),
            )

        self.assertEqual(assignee.user_id, 9)
        self.assertEqual(assignee.user_name, "审核人")
        mock_resolve_org.assert_called_once()
        mock_applicant_relation.assert_not_called()
        mock_relation_filter.assert_called_once_with(
            org_id=88,
            status=UserOrgRelation.Status.NORMAL,
            employee_level__in=["L1"],
        )

    @patch("apps.workflow.runtime.WfTask.objects.filter")
    def test_resolve_org_id_from_source_task_uses_previous_task_assignee_when_missing_on_source_task(self, mock_task_filter):
        service = WorkflowRuntimeService()
        history_task = SimpleNamespace(assignee_id=7)
        task_queryset = MagicMock()
        task_queryset.first.return_value = history_task
        mock_task_filter.return_value = task_queryset

        with patch.object(service, "_get_user_primary_relation", return_value=SimpleNamespace(org_id=66)) as mock_relation:
            org_id = service._resolve_org_id_from_source_task(SimpleNamespace(id=301))

        self.assertEqual(org_id, 66)
        mock_task_filter.assert_called_once_with(id=301)
        mock_relation.assert_called_once_with(7)

    @patch("apps.workflow.runtime.User.objects.filter")
    @patch("apps.workflow.runtime.UserOrgRelation.objects.filter")
    def test_resolve_team_based_assignee_uses_source_team_and_returns_first_match(
        self,
        mock_relation_filter,
        mock_user_filter,
    ):
        service = WorkflowRuntimeService()
        instance = SimpleNamespace(id=101, process_def_id=11, applicant_id=1)
        node = SimpleNamespace(node_code="rpt_submit_checker", node_name="单位复核人")
        rule = SimpleNamespace(rule_type="employee_level", rule_value="13,23")
        source_relation = SimpleNamespace(team_org_code="TEAM001", team_name="零售一组")
        candidate_relations = [
            SimpleNamespace(user_id=9),
            SimpleNamespace(user_id=8),
        ]
        first_user = SimpleNamespace(id=9, full_name="复核人甲")
        second_user = SimpleNamespace(id=8, full_name="复核人乙")

        source_relation_queryset = MagicMock()
        source_relation_ordered = MagicMock()
        source_relation_queryset.order_by.return_value = source_relation_ordered
        source_relation_ordered.first.return_value = source_relation

        candidate_relation_queryset = MagicMock()
        candidate_relation_queryset.order_by.return_value = candidate_relations

        mock_relation_filter.side_effect = [source_relation_queryset, candidate_relation_queryset]
        mock_user_filter.return_value = [first_user, second_user]

        with patch.object(service, "_get_rule", return_value=rule):
            assignee = service._resolve_team_based_assignee(
                instance=instance,
                node=node,
                branch_key="org_88",
                source_task=SimpleNamespace(id=301, assignee_id=7),
            )

        self.assertEqual(assignee.user_id, 9)
        self.assertEqual(assignee.user_name, "复核人甲")
        self.assertEqual(mock_relation_filter.call_count, 2)
        mock_relation_filter.assert_any_call(
            user_id=7,
            org_id=88,
            status=UserOrgRelation.Status.NORMAL,
        )
        mock_relation_filter.assert_any_call(
            org_id=88,
            status=UserOrgRelation.Status.NORMAL,
            employee_level__in=["13", "23"],
            team_name="零售一组",
        )

    @patch("apps.workflow.runtime.User.objects.filter")
    @patch("apps.workflow.runtime.UserOrgRelation.objects.filter")
    def test_resolve_team_based_assignee_rejects_when_no_candidate_found(
        self,
        mock_relation_filter,
        mock_user_filter,
    ):
        service = WorkflowRuntimeService()
        instance = SimpleNamespace(id=101, process_def_id=11, applicant_id=1)
        node = SimpleNamespace(node_code="rpt_submit_checker", node_name="单位复核人")
        rule = SimpleNamespace(rule_type="employee_level", rule_value="13")
        source_relation = SimpleNamespace(team_org_code=None, team_name="零售一组")

        source_relation_queryset = MagicMock()
        source_relation_ordered = MagicMock()
        source_relation_queryset.order_by.return_value = source_relation_ordered
        source_relation_ordered.first.return_value = source_relation

        candidate_relation_queryset = MagicMock()
        candidate_relation_queryset.order_by.return_value = []

        mock_relation_filter.side_effect = [source_relation_queryset, candidate_relation_queryset]
        mock_user_filter.return_value = []

        with patch.object(service, "_get_rule", return_value=rule):
            with self.assertRaises(ValidationError) as ctx:
                service._resolve_team_based_assignee(
                    instance=instance,
                    node=node,
                    branch_key="org_88",
                    source_task=SimpleNamespace(id=301, assignee_id=7),
                )

        self.assertEqual(
            ctx.exception.detail["message"],
            "节点[单位复核人]未找到符合条件的审批人，请管理员配置",
        )
        mock_relation_filter.assert_any_call(
            org_id=88,
            status=UserOrgRelation.Status.NORMAL,
            employee_level__in=["13"],
            team_name="零售一组",
        )

    def test_report_confirm_checker_returns_next_assignment_for_source_branch(self):
        service = WorkflowRuntimeService()
        instance = SimpleNamespace(id=101, process_def_id=11)
        auto_node = SimpleNamespace(node_code="rpt_submit_checker_confirm", node_name="确认单位复核人")
        source_task = SimpleNamespace(branch_key="org_88", parallel_group="group_1", assignee_id=7)
        transition = SimpleNamespace(to_node_code="rpt_submit_checker")
        checker_node = SimpleNamespace(node_code="rpt_submit_checker", node_name="单位复核人")

        with patch.object(service, "_get_available_transitions", return_value=[transition]) as mock_transitions, patch.object(
            service,
            "_get_node",
            return_value=checker_node,
        ), patch.object(
            service,
            "_resolve_team_based_assignee",
            return_value=SimpleNamespace(user_id=9, user_name="复核人甲"),
        ) as mock_resolve:
            result = service.report_confirm_checker(
                instance=instance,
                node=auto_node,
                source_task=source_task,
                context={"foo": "bar"},
            )

        self.assertEqual(result["context"], {"foo": "bar"})
        self.assertEqual(
            result["next_assignments"],
            [
                {
                    "branch_key": "org_88",
                    "parallel_group": "group_1",
                    "explicit_assignee": SimpleNamespace(user_id=9, user_name="复核人甲"),
                }
            ],
        )
        mock_transitions.assert_called_once_with(
            process_def_id=11,
            from_node_code="rpt_submit_checker_confirm",
            action_code="auto",
            context={"foo": "bar"},
        )
        mock_resolve.assert_called_once_with(
            instance=instance,
            node=checker_node,
            branch_key="org_88",
            source_task=source_task,
        )

    def test_assign_personal_line_assignee_sets_explicit_assignee_in_context(self):
        service = WorkflowRuntimeService()
        instance = SimpleNamespace(id=101, process_def_id=11)
        auto_node = SimpleNamespace(node_code="perf_claim_operator_assign", node_name="自动确认经办人")
        transition = SimpleNamespace(to_node_code="perf_claim_operator")
        operator_node = SimpleNamespace(node_code="perf_claim_operator", node_name="经办人")
        assignee = SimpleNamespace(user_id=9, user_name="经办人甲")

        with patch.object(service, "_get_available_transitions", return_value=[transition]) as mock_transitions, patch.object(
            service,
            "_get_node",
            return_value=operator_node,
        ), patch.object(
            service,
            "_resolve_personal_line_assignee",
            return_value=assignee,
        ) as mock_resolve:
            result = service.assign_personal_line_assignee(
                instance=instance,
                node=auto_node,
                source_task=SimpleNamespace(branch_key="org_88", parallel_group="group_1"),
                context={"foo": "bar"},
            )

        self.assertEqual(
            result,
            {
                "context": {"foo": "bar", "_explicit_assignee": assignee},
                "target_node_code": "perf_claim_operator",
            },
        )
        mock_transitions.assert_called_once_with(
            process_def_id=11,
            from_node_code="perf_claim_operator_assign",
            action_code="auto",
            context={"foo": "bar"},
        )
        mock_resolve.assert_called_once_with(instance=instance, node=operator_node)

    @patch("apps.workflow.runtime.User.objects.filter")
    @patch("apps.workflow.runtime.UserOrgRelation.objects.filter")
    @patch("apps.workflow.runtime.OrgUnit.objects.filter")
    def test_resolve_personal_line_assignee_uses_line_org_code_and_personal_line_team(
        self,
        mock_org_filter,
        mock_relation_filter,
        mock_user_filter,
    ):
        service = WorkflowRuntimeService()
        instance = SimpleNamespace(id=101)
        node = SimpleNamespace(node_name="经办人")

        org_queryset = MagicMock()
        org_queryset.first.return_value = SimpleNamespace(id=88)
        mock_org_filter.return_value = org_queryset

        relation_queryset = MagicMock()
        relation_ordered = MagicMock()
        relation_values = MagicMock()
        relation_distinct = [9]
        relation_queryset.order_by.return_value = relation_ordered
        relation_ordered.values_list.return_value = relation_values
        relation_values.distinct.return_value = relation_distinct
        mock_relation_filter.return_value = relation_queryset

        user_queryset = MagicMock()
        user_queryset.order_by.return_value = [SimpleNamespace(id=9, full_name="经办人甲")]
        mock_user_filter.return_value = user_queryset

        with patch.object(service, "_get_instance_line_org_code", return_value="44030001") as mock_line_org:
            assignee = service._resolve_personal_line_assignee(instance=instance, node=node)

        self.assertEqual(assignee.user_id, 9)
        self.assertEqual(assignee.user_name, "经办人甲")
        mock_line_org.assert_called_once_with(101)
        mock_org_filter.assert_called_once_with(org_code="44030001", status="01")
        mock_relation_filter.assert_called_once_with(
            org_id=88,
            status=UserOrgRelation.Status.NORMAL,
            team_name__icontains="个人条线",
        )
        mock_user_filter.assert_called_once_with(id__in=[9], user_status=User.Status.NORMAL)

    @patch("apps.workflow.runtime.User.objects.filter")
    @patch("apps.workflow.runtime.UserOrgRelation.objects.filter")
    @patch("apps.workflow.runtime.OrgUnit.objects.filter")
    def test_resolve_personal_line_assignee_rejects_multiple_users(
        self,
        mock_org_filter,
        mock_relation_filter,
        mock_user_filter,
    ):
        service = WorkflowRuntimeService()
        instance = SimpleNamespace(id=101)
        node = SimpleNamespace(node_name="经办人")

        mock_org_filter.return_value.first.return_value = SimpleNamespace(id=88)

        relation_queryset = MagicMock()
        relation_ordered = MagicMock()
        relation_values = MagicMock()
        relation_queryset.order_by.return_value = relation_ordered
        relation_ordered.values_list.return_value = relation_values
        relation_values.distinct.return_value = [9, 10]
        mock_relation_filter.return_value = relation_queryset

        user_queryset = MagicMock()
        user_queryset.order_by.return_value = [
            SimpleNamespace(id=9, full_name="经办人甲"),
            SimpleNamespace(id=10, full_name="经办人乙"),
        ]
        mock_user_filter.return_value = user_queryset

        with patch.object(service, "_get_instance_line_org_code", return_value="44030001"):
            with self.assertRaises(ValidationError) as ctx:
                service._resolve_personal_line_assignee(instance=instance, node=node)

        self.assertEqual(
            ctx.exception.detail["message"],
            "节点[经办人]找到多个个人条线审批人，请管理员修改配置",
        )

    def test_process_transition_passes_explicit_assignee_to_join_target_node(self):
        service = WorkflowRuntimeService()
        instance = SimpleNamespace(process_def_id=11)
        transition = SimpleNamespace(to_node_code="perf_transfer_operator")
        target_node = SimpleNamespace(node_code="perf_transfer_operator", join_strategy="all_pass")
        operator = SimpleNamespace(id=1, full_name="操作人")
        source_task = SimpleNamespace(
            id=301,
            instance_id=101,
            node_code="perf_transfer_operator_assign",
            branch_key="org_88",
            parallel_group="group_1",
        )
        assignee = SimpleNamespace(user_id=9, user_name="经办人甲")

        with patch.object(service, "_get_node", return_value=target_node), patch.object(
            service,
            "_has_pending_parallel_sibling",
            return_value=False,
        ), patch.object(service, "_enter_node") as mock_enter:
            service._process_transition(
                instance=instance,
                transition=transition,
                operator=operator,
                source_task=source_task,
                context={"_explicit_assignee": assignee},
            )

        mock_enter.assert_called_once_with(
            instance=instance,
            node=target_node,
            operator=operator,
            source_task=source_task,
            branch_key=None,
            parallel_group="group_1",
            context={"parallel_group": "group_1"},
            explicit_assignee=assignee,
            prefer_existing_assignee=False,
        )
