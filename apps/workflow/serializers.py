from django.db import transaction
from django.db.models import Max, Q
from rest_framework import serializers

from common.serializers import IgnoreExtraFieldsMixin

from .models import (
    InstanceStatus,
    ProcessBusinessType,
    TaskStatus,
    TransitionActionCode,
    WfApprovalAssignment,
    WfNodeAssigneeRule,
    WfNodeDef,
    WfProcessDef,
    WfTask,
    WfTaskLog,
    WfTransitionDef,
    WfInstance,
)


def _validate_process_def_exists(process_def_id):
    if not WfProcessDef.objects.filter(id=process_def_id).exists():
        raise serializers.ValidationError("流程定义不存在")
    return process_def_id


def _validate_node_exists(process_def_id, node_code, field_name):
    exists = WfNodeDef.objects.filter(process_def_id=process_def_id, node_code=node_code).exists()
    if not exists:
        raise serializers.ValidationError({field_name: ["节点不存在"]})


def _get_next_process_version(process_code):
    max_version = WfProcessDef.objects.filter(process_code=process_code).aggregate(max_version=Max("version"))["max_version"]
    return (max_version or 0) + 1


class WfProcessDefSerializer(IgnoreExtraFieldsMixin, serializers.ModelSerializer):
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    node_count = serializers.IntegerField(read_only=True)
    assignee_rule_count = serializers.IntegerField(read_only=True)
    transition_count = serializers.IntegerField(read_only=True)
    version = serializers.IntegerField(required=False)
    empty_to_none_fields = {"remark"}

    class Meta:
        model = WfProcessDef
        fields = [
            "id",
            "process_code",
            "process_name",
            "business_type",
            "version",
            "status",
            "status_label",
            "is_latest",
            "remark",
            "node_count",
            "assignee_rule_count",
            "transition_count",
            "created_at",
            "updated_at",
        ]
        validators = []
        read_only_fields = [
            "id",
            "status_label",
            "node_count",
            "assignee_rule_count",
            "transition_count",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "remark": {"required": False, "allow_null": True, "allow_blank": True},
        }

    def validate(self, attrs):
        process_code = attrs.get("process_code", getattr(self.instance, "process_code", None))
        version = attrs.get("version")

        if version is None:
            if self.instance is not None:
                version = getattr(self.instance, "version", None)
            else:
                version = _get_next_process_version(process_code)
                attrs["version"] = version

        duplicated_queryset = WfProcessDef.objects.filter(process_code=process_code, version=version)
        if self.instance is not None:
            duplicated_queryset = duplicated_queryset.exclude(id=self.instance.id)
        if duplicated_queryset.exists():
            raise serializers.ValidationError({"version": ["同一流程编码下版本号不能重复"]})
        return attrs

    @staticmethod
    def _sync_latest_flag(process_code, current_id):
        WfProcessDef.objects.filter(process_code=process_code, is_latest=True).exclude(id=current_id).update(is_latest=False)

    def create(self, validated_data):
        with transaction.atomic():
            instance = super().create(validated_data)
            if instance.is_latest:
                self._sync_latest_flag(instance.process_code, instance.id)
        return instance

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            if instance.is_latest:
                self._sync_latest_flag(instance.process_code, instance.id)
        return instance


class WfNodeDefSerializer(IgnoreExtraFieldsMixin, serializers.ModelSerializer):
    node_type_label = serializers.CharField(source="get_node_type_display", read_only=True)
    join_strategy_label = serializers.CharField(source="get_join_strategy_display", read_only=True)
    empty_to_none_fields = {"parallel_mode", "join_strategy", "remark"}

    class Meta:
        model = WfNodeDef
        fields = [
            "id",
            "process_def_id",
            "node_code",
            "node_name",
            "node_type",
            "node_type_label",
            "node_order",
            "is_parallel",
            "parallel_mode",
            "join_strategy",
            "join_strategy_label",
            "can_reject",
            "can_return",
            "auto_create_task",
            "remark",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "node_type_label",
            "join_strategy_label",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "node_order": {"required": False, "allow_null": True},
            "parallel_mode": {"required": False, "allow_null": True, "allow_blank": True},
            "join_strategy": {"required": False, "allow_null": True, "allow_blank": True},
            "remark": {"required": False, "allow_null": True, "allow_blank": True},
        }

    def validate_process_def_id(self, value):
        return _validate_process_def_exists(value)

    def validate(self, attrs):
        process_def_id = attrs.get("process_def_id", getattr(self.instance, "process_def_id", None))
        node_code = attrs.get("node_code", getattr(self.instance, "node_code", None))

        duplicated_queryset = WfNodeDef.objects.filter(process_def_id=process_def_id, node_code=node_code)
        if self.instance is not None:
            duplicated_queryset = duplicated_queryset.exclude(id=self.instance.id)
        if duplicated_queryset.exists():
            raise serializers.ValidationError({"node_code": ["同一流程定义下节点编码不能重复"]})
        return attrs

    def update(self, instance, validated_data):
        old_process_def_id = instance.process_def_id
        old_node_code = instance.node_code
        new_process_def_id = validated_data.get("process_def_id", old_process_def_id)
        new_node_code = validated_data.get("node_code", old_node_code)

        if old_process_def_id != new_process_def_id:
            is_referenced = (
                WfNodeAssigneeRule.objects.filter(process_def_id=old_process_def_id, node_code=old_node_code).exists()
                or WfTransitionDef.objects.filter(process_def_id=old_process_def_id)
                .filter(Q(from_node_code=old_node_code) | Q(to_node_code=old_node_code))
                .exists()
            )
            if is_referenced:
                raise serializers.ValidationError(
                    {"process_def_id": ["当前节点已被审批人规则或流转定义引用，不允许变更所属流程定义"]}
                )

        with transaction.atomic():
            instance = super().update(instance, validated_data)
            if old_node_code != new_node_code:
                WfNodeAssigneeRule.objects.filter(
                    process_def_id=old_process_def_id,
                    node_code=old_node_code,
                ).update(node_code=new_node_code)
                WfTransitionDef.objects.filter(
                    process_def_id=old_process_def_id,
                    from_node_code=old_node_code,
                ).update(from_node_code=new_node_code)
                WfTransitionDef.objects.filter(
                    process_def_id=old_process_def_id,
                    to_node_code=old_node_code,
                ).update(to_node_code=new_node_code)
        return instance


class WfTransitionDefSerializer(IgnoreExtraFieldsMixin, serializers.ModelSerializer):
    from_node_name = serializers.CharField(read_only=True)
    to_node_name = serializers.CharField(read_only=True)
    action_code_label = serializers.CharField(source="get_action_code_display", read_only=True)
    condition_type_label = serializers.CharField(source="get_condition_type_display", read_only=True)
    empty_to_none_fields = {"condition_type", "condition_expr", "remark"}

    class Meta:
        model = WfTransitionDef
        fields = [
            "id",
            "process_def_id",
            "from_node_code",
            "from_node_name",
            "to_node_code",
            "to_node_name",
            "action_code",
            "action_code_label",
            "condition_type",
            "condition_type_label",
            "condition_expr",
            "priority",
            "is_enabled",
            "remark",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "from_node_name",
            "to_node_name",
            "action_code_label",
            "condition_type_label",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "condition_type": {"required": False, "allow_null": True, "allow_blank": True},
            "condition_expr": {"required": False, "allow_null": True, "allow_blank": True},
            "remark": {"required": False, "allow_null": True, "allow_blank": True},
        }

    def validate_process_def_id(self, value):
        return _validate_process_def_exists(value)

    def validate(self, attrs):
        process_def_id = attrs.get("process_def_id", getattr(self.instance, "process_def_id", None))
        from_node_code = attrs.get("from_node_code", getattr(self.instance, "from_node_code", None))
        to_node_code = attrs.get("to_node_code", getattr(self.instance, "to_node_code", None))

        node_codes = set(
            WfNodeDef.objects.filter(process_def_id=process_def_id, node_code__in=[from_node_code, to_node_code]).values_list(
                "node_code",
                flat=True,
            )
        )
        errors = {}
        if from_node_code and from_node_code not in node_codes:
            errors["from_node_code"] = ["来源节点不存在"]
        if to_node_code and to_node_code not in node_codes:
            errors["to_node_code"] = ["目标节点不存在"]
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class WfNodeAssigneeRuleSerializer(IgnoreExtraFieldsMixin, serializers.ModelSerializer):
    node_name = serializers.CharField(read_only=True)
    rule_type_label = serializers.CharField(source="get_rule_type_display", read_only=True)
    empty_to_none_fields = {"rule_value", "remark"}

    class Meta:
        model = WfNodeAssigneeRule
        fields = [
            "id",
            "process_def_id",
            "node_code",
            "node_name",
            "rule_type",
            "rule_type_label",
            "rule_value",
            "remark",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "node_name",
            "rule_type_label",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "rule_value": {"required": False, "allow_null": True, "allow_blank": True},
            "remark": {"required": False, "allow_null": True, "allow_blank": True},
        }

    def validate_process_def_id(self, value):
        return _validate_process_def_exists(value)

    def validate(self, attrs):
        process_def_id = attrs.get("process_def_id", getattr(self.instance, "process_def_id", None))
        node_code = attrs.get("node_code", getattr(self.instance, "node_code", None))
        if process_def_id and node_code:
            _validate_node_exists(process_def_id, node_code, "node_code")
        return attrs


class WfInstanceStartSerializer(IgnoreExtraFieldsMixin, serializers.Serializer):
    process_def_id = serializers.IntegerField()
    title = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=200)
    business_id = serializers.IntegerField(required=False, allow_null=True)
    empty_to_none_fields = {"title"}


class WfTaskActionSerializer(IgnoreExtraFieldsMixin, serializers.Serializer):
    action_code = serializers.ChoiceField(choices=TransitionActionCode.choices)
    comment = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=1000)
    selected_user_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=True,
    )
    target_branch_key = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=100)
    empty_to_none_fields = {"comment", "target_branch_key"}


class WfTaskSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    result_label = serializers.CharField(source="get_result_display", read_only=True)
    branch_org_id = serializers.SerializerMethodField()
    branch_org_name = serializers.SerializerMethodField()
    process_def_id = serializers.SerializerMethodField()
    instance_title = serializers.SerializerMethodField()

    class Meta:
        model = WfTask
        fields = [
            "id",
            "instance_id",
            "instance_title",
            "process_def_id",
            "node_code",
            "node_name",
            "assignee_id",
            "assignee_name",
            "branch_key",
            "branch_org_id",
            "branch_org_name",
            "parallel_group",
            "status",
            "status_label",
            "result",
            "result_label",
            "round_no",
            "completed_at",
            "created_at",
            "updated_at",
        ]

    def get_branch_org_id(self, obj):
        return getattr(obj, "branch_org_id", None)

    def get_branch_org_name(self, obj):
        return getattr(obj, "branch_org_name", None)

    def get_process_def_id(self, obj):
        return getattr(obj, "process_def_id", None)

    def get_instance_title(self, obj):
        return getattr(obj, "instance_title", None)


class WfTaskLogSerializer(serializers.ModelSerializer):
    action_label = serializers.CharField(source="get_action_display", read_only=True)
    result_label = serializers.CharField(source="get_result_display", read_only=True)

    class Meta:
        model = WfTaskLog
        fields = [
            "id",
            "instance_id",
            "task_id",
            "branch_key",
            "parallel_group",
            "action",
            "action_label",
            "from_node_code",
            "from_node_name",
            "to_node_code",
            "to_node_name",
            "operator_id",
            "operator_name",
            "result",
            "result_label",
            "comment",
            "created_at",
            "updated_at",
        ]


class WfApprovalAssignmentSerializer(serializers.ModelSerializer):
    result_label = serializers.CharField(source="get_result_display", read_only=True)
    instance_title = serializers.SerializerMethodField()
    process_def_id = serializers.SerializerMethodField()
    process_name = serializers.SerializerMethodField()
    business_type = serializers.SerializerMethodField()
    business_type_label = serializers.SerializerMethodField()
    business_id = serializers.SerializerMethodField()
    instance_status = serializers.SerializerMethodField()
    instance_status_label = serializers.SerializerMethodField()
    start_time = serializers.SerializerMethodField()
    end_time = serializers.SerializerMethodField()
    applicant_id = serializers.SerializerMethodField()
    applicant_name = serializers.SerializerMethodField()
    cust_name = serializers.SerializerMethodField()
    ecif_cust_id = serializers.SerializerMethodField()
    accounting_org_id = serializers.SerializerMethodField()
    accounting_org_name = serializers.SerializerMethodField()
    task_status = serializers.SerializerMethodField()
    task_status_label = serializers.SerializerMethodField()
    branch_key = serializers.SerializerMethodField()
    branch_org_id = serializers.SerializerMethodField()
    branch_org_name = serializers.SerializerMethodField()

    class Meta:
        model = WfApprovalAssignment
        fields = [
            "id",
            "instance_id",
            "instance_title",
            "process_def_id",
            "process_name",
            "business_type",
            "business_type_label",
            "business_id",
            "instance_status",
            "instance_status_label",
            "start_time",
            "end_time",
            "applicant_id",
            "applicant_name",
            "task_id",
            "node_code",
            "node_name",
            "assignee_id",
            "assignee_name",
            "round_no",
            "task_status",
            "task_status_label",
            "branch_key",
            "branch_org_id",
            "branch_org_name",
            "cust_name",
            "ecif_cust_id",
            "accounting_org_id",
            "accounting_org_name",
            "result",
            "result_label",
            "received_at",
            "read_at",
            "handled_at",
            "comment",
            "created_at",
            "updated_at",
        ]

    def get_instance_title(self, obj):
        return getattr(obj, "instance_title", None)

    def get_process_def_id(self, obj):
        return getattr(obj, "process_def_id", None)

    def get_process_name(self, obj):
        return getattr(obj, "process_name", None)

    def get_business_type(self, obj):
        return getattr(obj, "business_type", None)

    def get_business_type_label(self, obj):
        business_type = getattr(obj, "business_type", None)
        if not business_type:
            return None
        return dict(ProcessBusinessType.choices).get(business_type)

    def get_business_id(self, obj):
        return getattr(obj, "business_id", None)

    def get_instance_status(self, obj):
        return getattr(obj, "instance_status", None)

    def get_instance_status_label(self, obj):
        instance_status = getattr(obj, "instance_status", None)
        if not instance_status:
            return None
        return dict(InstanceStatus.choices).get(instance_status)

    def get_start_time(self, obj):
        return getattr(obj, "start_time", None)

    def get_end_time(self, obj):
        return getattr(obj, "end_time", None)

    def get_applicant_id(self, obj):
        return getattr(obj, "applicant_id", None)

    def get_applicant_name(self, obj):
        return getattr(obj, "applicant_name", None)

    def get_cust_name(self, obj):
        return getattr(obj, "cust_name", None)

    def get_ecif_cust_id(self, obj):
        return getattr(obj, "ecif_cust_id", None)

    def get_accounting_org_id(self, obj):
        return getattr(obj, "accounting_org_id", None)

    def get_accounting_org_name(self, obj):
        return getattr(obj, "accounting_org_name", None)

    def get_task_status(self, obj):
        return getattr(obj, "task_status", None)

    def get_task_status_label(self, obj):
        task_status = getattr(obj, "task_status", None)
        if not task_status:
            return None
        return dict(TaskStatus.choices).get(task_status)

    def get_branch_key(self, obj):
        return getattr(obj, "branch_key", None)

    def get_branch_org_id(self, obj):
        return getattr(obj, "branch_org_id", None)

    def get_branch_org_name(self, obj):
        return getattr(obj, "branch_org_name", None)


class WfInstanceSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    process_name = serializers.SerializerMethodField()
    task_count = serializers.IntegerField(read_only=True)
    active_task_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = WfInstance
        fields = [
            "id",
            "title",
            "process_def_id",
            "process_name",
            "business_type",
            "business_id",
            "applicant_id",
            "applicant_name",
            "current_node_code",
            "current_node_name",
            "status",
            "status_label",
            "task_count",
            "active_task_count",
            "start_time",
            "end_time",
            "created_at",
            "updated_at",
        ]

    def get_process_name(self, obj):
        return getattr(obj, "process_name", None)
