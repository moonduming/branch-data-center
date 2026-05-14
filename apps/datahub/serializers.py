from django.db import transaction
from rest_framework import serializers

from common.serializers import IgnoreExtraFieldsMixin

from .models import (
    DataImportLog,
    PerfIndicator,
    PerfIndicatorRule,
    ResultImportIndicatorLogPostProfit,
    ResultImportLog,
)


MAX_INDICATOR_LEVEL = 2


def get_indicator_parent_chain(parent_id):
    chain = []
    visited = set()
    current_parent_id = parent_id

    while current_parent_id is not None:
        if current_parent_id in visited:
            raise serializers.ValidationError({'parent_id': ['指标层级存在循环引用']})

        parent = PerfIndicator.objects.filter(id=current_parent_id).only('id', 'parent_id').first()
        if parent is None:
            raise serializers.ValidationError({'parent_id': ['父指标不存在']})

        chain.append(parent)
        visited.add(current_parent_id)
        current_parent_id = parent.parent_id

    return chain

class PerfIndicatorSerializer(IgnoreExtraFieldsMixin, serializers.ModelSerializer):
    drop_empty_fields = {'parent_id'}
    empty_to_none_fields = {
        'assessment_indicator_id',
        'category_code',
        'category_name',
        'line_code',
        'display_unit',
        'description',
        'remark',
    }

    class Meta:
        model = PerfIndicator
        fields = [
            'id',
            'indicator_code',
            'indicator_name',
            'parent_id',
            'assessment_indicator_id',
            'category_code',
            'category_name',
            'line_code',
            'indicator_standard',
            'display_unit',
            'decimal_places',
            'display_type',
            'display_scope',
            'show_in_card',
            'show_in_trend',
            'show_in_rank',
            'sort_no',
            'status',
            'description',
            'remark',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
        ]
        extra_kwargs = {
            'parent_id': {'required': False, 'allow_null': True},
            'assessment_indicator_id': {'required': False, 'allow_null': True, 'allow_blank': True},
            'category_code': {'required': False, 'allow_null': True, 'allow_blank': True},
            'category_name': {'required': False, 'allow_null': True, 'allow_blank': True},
            'line_code': {'required': False, 'allow_null': True, 'allow_blank': True},
            'display_unit': {'required': False, 'allow_null': True, 'allow_blank': True},
            'description': {'required': False, 'allow_null': True, 'allow_blank': True},
            'remark': {'required': False, 'allow_null': True, 'allow_blank': True},
        }

    def validate(self, attrs):
        if 'parent_id' in attrs:
            parent_id = attrs.get('parent_id')
        elif self.instance is not None:
            parent_id = self.instance.parent_id
        else:
            parent_id = None

        if self.instance is not None and parent_id == self.instance.id:
            raise serializers.ValidationError({'parent_id': ['父指标不能是自己']})

        chain = get_indicator_parent_chain(parent_id)
        ancestor_ids = {item.id for item in chain}

        if self.instance is not None and self.instance.id in ancestor_ids:
            raise serializers.ValidationError({'parent_id': ['父指标不能设置为当前指标的子孙节点']})

        if len(chain) >= MAX_INDICATOR_LEVEL:
            raise serializers.ValidationError({'parent_id': [f'指标层级最多支持 {MAX_INDICATOR_LEVEL} 级']})

        return attrs


class PerfIndicatorRuleSerializer(IgnoreExtraFieldsMixin, serializers.ModelSerializer):
    indicator_code = serializers.CharField(read_only=True)
    indicator_name = serializers.CharField(read_only=True)

    drop_empty_fields = {'rule_version'}
    empty_to_none_fields = {
        'rule_name',
        'target_sql_template',
        'data_source_desc',
        'compare_value_field',
        'org_prefix',
        'remark',
    }

    class Meta:
        model = PerfIndicatorRule
        fields = [
            'id',
            'indicator_id',
            'indicator_code',
            'indicator_name',
            'rule_version',
            'is_current',
            'rule_name',
            'sql_template',
            'target_sql_template',
            'calc_mode',
            'result_fields',
            'org_prefix',
            'need_org_filter',
            'need_date_param',
            'need_day_count_param',
            'run_mode',
            'data_source_desc',
            'display_value_field',
            'compare_value_field',
            'status',
            'remark',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'indicator_code', 'indicator_name', 'created_at', 'updated_at']
        extra_kwargs = {
            'rule_name': {'required': False, 'allow_null': True, 'allow_blank': True},
            'target_sql_template': {'required': False, 'allow_null': True, 'allow_blank': True},
            'data_source_desc': {'required': False, 'allow_null': True, 'allow_blank': True},
            'compare_value_field': {'required': False, 'allow_null': True, 'allow_blank': True},
            'org_prefix': {'required': False, 'allow_null': True, 'allow_blank': True},
            'remark': {'required': False, 'allow_null': True, 'allow_blank': True},
        }

    def validate_indicator_id(self, value):
        if not PerfIndicator.objects.filter(id=value).exists():
            raise serializers.ValidationError('指标不存在')
        return value

    def validate(self, attrs):
        indicator_id = attrs.get('indicator_id', self.instance.indicator_id if self.instance else None)
        rule_version = attrs.get('rule_version', self.instance.rule_version if self.instance else None)

        duplicated_queryset = PerfIndicatorRule.objects.filter(
            indicator_id=indicator_id,
            rule_version=rule_version,
        )
        if self.instance is not None:
            duplicated_queryset = duplicated_queryset.exclude(id=self.instance.id)

        if duplicated_queryset.exists():
            raise serializers.ValidationError({'rule_version': ['同一指标下规则版本号不能重复']})

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        instance = super().create(validated_data)
        self._sync_current_flag(instance)
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        self._sync_current_flag(instance)
        return instance

    def _sync_current_flag(self, instance):
        if instance.is_current:
            PerfIndicatorRule.objects.filter(indicator_id=instance.indicator_id).exclude(id=instance.id).update(
                is_current=False
            )


class PerfIndicatorDashboardQuerySerializer(serializers.Serializer):
    data_dt = serializers.DateField(required=True)
    parent_indicator_id = serializers.IntegerField(required=True, min_value=1)
    org_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class PerfIndicatorPersonalDashboardQuerySerializer(PerfIndicatorDashboardQuerySerializer):
    employee_no = serializers.CharField(required=True, allow_blank=False, max_length=32)


class PerfIndicatorPersonalPropStatusQuerySerializer(serializers.Serializer):
    employee_no = serializers.CharField(required=True, allow_blank=False, max_length=32)


class DataImportLogQuerySerializer(serializers.Serializer):
    data_dt = serializers.DateField(required=False)


class DataImportLogSerializer(serializers.ModelSerializer):
    status_label = serializers.SerializerMethodField()

    class Meta:
        model = DataImportLog
        fields = [
            'id',
            'file_name',
            'data_date',
            'run_count',
            'status',
            'status_label',
            'message',
            'created_at',
            'updated_at',
        ]

    def get_status_label(self, obj):
        return obj.get_status_display() or '未知'


class ResultImportLogSerializer(serializers.ModelSerializer):
    status_label = serializers.SerializerMethodField()

    class Meta:
        model = ResultImportLog
        fields = [
            'id',
            'data_date',
            'status',
            'status_label',
            'message',
            'created_at',
            'updated_at',
        ]

    def get_status_label(self, obj):
        return obj.get_status_display() or '未知'


class ResultImportIndicatorLogPostProfitSerializer(serializers.ModelSerializer):
    status_label = serializers.SerializerMethodField()

    class Meta:
        model = ResultImportIndicatorLogPostProfit
        fields = [
            'id',
            'data_date',
            'indicator_id',
            'rule_id',
            'status',
            'status_label',
            'message',
            'created_at',
            'updated_at',
        ]

    def get_status_label(self, obj):
        return obj.get_status_display() or '未知'
