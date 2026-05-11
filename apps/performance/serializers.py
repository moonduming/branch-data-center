import calendar
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from .models import ShenzhenPropStatus, AcctSumDHistory, AcctSumMHistory, PropStatusFlg

from common.serializers import IgnoreExtraFieldsMixin
from ..users.models import User
from ..workflow.models import (
    ProcessBusinessType, ProcessDefStatus, 
    TransitionActionCode, WfProcessDef
)


class ShenzhenPropStatusSerializer(IgnoreExtraFieldsMixin, serializers.ModelSerializer):
    prop_status_flg_label = serializers.CharField(source="get_prop_status_flg_display", read_only=True)

    class Meta:
        model = ShenzhenPropStatus
        fields = "__all__"


class WorkflowItemSerializer(IgnoreExtraFieldsMixin, serializers.Serializer):
    user_id = serializers.IntegerField(required=True)
    kpi_prop = serializers.DecimalField(max_digits=7, decimal_places=4, required=True)
    cust_name = serializers.CharField(required=True, allow_blank=True)
    genr_acct_id = serializers.CharField(required=True, allow_blank=True)
    ecif_cust_id = serializers.CharField(required=True, allow_blank=True)
    orig_acct_id = serializers.CharField(required=True, allow_blank=True)
    accnt_org_id = serializers.CharField(required=True, allow_blank=True)
    accnt_org_name = serializers.CharField(required=True, allow_blank=True)
    org_code = serializers.CharField(required=True, allow_blank=True)


class CreateWorkflowSerializer(IgnoreExtraFieldsMixin, serializers.Serializer):
    business_type = serializers.ChoiceField(
        choices=[
            ProcessBusinessType.PERFORMANCE_CLAIM,
            ProcessBusinessType.PERFORMANCE_TRANSFER,
        ],
        required=True
    )
    data_dt = serializers.DateField()
    items = WorkflowItemSerializer(many=True, required=True, allow_empty=False)
    title = serializers.CharField(required=True, max_length=200)
    org_id = serializers.IntegerField(required=True)
    business_id = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=100)
    empty_to_none_fields = {"business_id"}

    def validate_data_dt(self, value):
        today = timezone.localdate()
        # 数据日期不能大于当前日期
        if value > today:
            raise serializers.ValidationError("数据日期不能大于当前日期")
        return value

    def validate_items(self, value):
        user_ids = [item["user_id"] for item in value]
        existing_user_ids = set(
            User.objects.filter(id__in=user_ids, user_status=User.Status.NORMAL).values_list("id", flat=True)
        )
        missing_user_ids = [user_id for user_id in user_ids if user_id not in existing_user_ids]
        if missing_user_ids:
            raise serializers.ValidationError(f"用户不存在或不可用: {missing_user_ids}")
        return value

    def validate(self, attrs):
        today = timezone.localdate()
        min_date = today - timedelta(days=30)
        org_code = {item.get("org_code") for item in attrs["items"]}
        if len(org_code) > 1:
            raise serializers.ValidationError({"message": "条线机构编码必须一致"})
        grouped_kpi_props = {}
        for item in attrs["items"]:
            if item.get("kpi_prop") is None:
                continue
            group_key = item["genr_acct_id"]
            grouped_kpi_props[group_key] = grouped_kpi_props.get(group_key, Decimal("0")) + item["kpi_prop"]
        for genr_acct_id, kpi_total in grouped_kpi_props.items():
            if kpi_total != Decimal("100"):
                raise serializers.ValidationError(
                    {"message": f"客户[{genr_acct_id}]的业绩占比之和必须刚好等于100"}
                )

        requested_data_dt = attrs["data_dt"]

        # 如果日期早于当前日期30天，则调整为该日期所在月份的月末
        use_month_history = False
        effective_data_dt = requested_data_dt
        if requested_data_dt < min_date:
            current_month_last_day = calendar.monthrange(requested_data_dt.year, requested_data_dt.month)[1]
            effective_data_dt = requested_data_dt.replace(day=current_month_last_day)
            attrs["data_dt"] = effective_data_dt
            use_month_history = True

        history_model = AcctSumMHistory if use_month_history else AcctSumDHistory
        validated_items = []
        for index, item in enumerate(attrs["items"], start=1):
            existing_prop_status = ShenzhenPropStatus.objects.filter(
                genr_acct_id=item["genr_acct_id"]
            ).exclude(prop_status_flg=PropStatusFlg.INVALID).exists()

            if attrs["business_type"] == ProcessBusinessType.PERFORMANCE_CLAIM and existing_prop_status:
                raise serializers.ValidationError(
                    {"message": f"第{index}条账号已存在认领记录，只允许发起移交"}
                )
            if attrs["business_type"] == ProcessBusinessType.PERFORMANCE_TRANSFER and not existing_prop_status:
                raise serializers.ValidationError(
                    {"message": f"第{index}条账号暂无认领记录，不能发起移交"}
                )

            validated_item = dict(item)
            # 将前端传入的百分数（如50）转换为比例（0.5）再入库
            if validated_item.get("kpi_prop") is not None:
                validated_item["kpi_prop"] = (validated_item["kpi_prop"] / Decimal("100")).quantize(Decimal("0.0001"))
            if attrs["business_type"] == ProcessBusinessType.PERFORMANCE_TRANSFER:
                bal_year_accum = (
                    history_model.objects.filter(
                        data_dt=effective_data_dt,
                        ecif_cust_id=item["ecif_cust_id"],
                        orig_acct_id=item["orig_acct_id"],
                    )
                    .values_list("bal_year_accum", flat=True)
                    .first()
                )
                validated_item["year_base_amount"] = bal_year_accum or 0
            else:
                validated_item["year_base_amount"] = 0
            validated_items.append(validated_item)
        attrs["items"] = validated_items
            
        wf = WfProcessDef.objects.filter(
            business_type=attrs["business_type"],
            status=ProcessDefStatus.ACTIVE
        ).order_by("-version", "-id").first()
        if not wf:
            raise serializers.ValidationError("流程定义不存在")
        attrs["action_code"] = TransitionActionCode.SUBMIT
        attrs["process_def_id"] = wf.id

        return attrs
