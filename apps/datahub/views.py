from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Q, Sum
from django.utils.dateparse import parse_date
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsAdminUserLevel
from common.query import parse_bool_param
from ..organization.models import OrgUnit, UserOrgRelation

from .models import (
    DataImportLog,
    PerfIndicator,
    PerfIndicatorResult,
    PerfIndicatorRule,
    ResultImportLog,
)
from .serializers import (
    DataImportLogQuerySerializer,
    DataImportLogSerializer,
    PerfIndicatorDashboardQuerySerializer,
    PerfIndicatorRuleSerializer,
    PerfIndicatorSerializer,
    ResultImportIndicatorLogPostProfitSerializer,
    ResultImportLogSerializer,
)
from .services.data_backup import resolve_backup_date
from .services.import_pipeline import (
    get_missing_dependency_tables,
    list_result_import_dependencies,
    list_post_profit_indicator_logs,
    resolve_import_date,
)
from .tasks import (
    run_auto_load_data_backup_task,
    run_datahub_post_profit_result_import,
    run_datahub_result_import,
    run_head_office_import,
)

def parse_optional_date_param(value, field_name='data_dt'):
    if value in (None, ''):
        return None

    parsed = parse_date(str(value))
    if parsed is None:
        raise ValidationError({field_name: [f'{field_name}格式错误，应为YYYY-MM-DD']})
    return parsed


# 指标管理
class PerfIndicatorViewSet(viewsets.ModelViewSet):
    queryset = PerfIndicator.objects.all().order_by('sort_no', 'id')
    serializer_class = PerfIndicatorSerializer
    permission_classes = [IsAdminUserLevel]

    def get_queryset(self):
        queryset = super().get_queryset()
        status_value = self.request.query_params.get('status')
        category_code = self.request.query_params.get('category_code')
        parent_id = self.request.query_params.get('parent_id')
        indicator_code = self.request.query_params.get('indicator_code')
        indicator_name = self.request.query_params.get('indicator_name')

        if status_value:
            queryset = queryset.filter(status=status_value)
        if category_code:
            queryset = queryset.filter(category_code=category_code)
        if parent_id not in (None, ''):
            queryset = queryset.filter(parent_id=parent_id)
        if indicator_code:
            print(f"indicator_code: {indicator_code}")
            queryset = queryset.filter(indicator_code__icontains=indicator_code)
        if indicator_name:
            queryset = queryset.filter(indicator_name__icontains=indicator_name)

        return queryset

    def list(self, request, *args, **kwargs):
        nested = parse_bool_param(request.query_params.get('nested'), default=True)
        parent_id = request.query_params.get('parent_id')

        if not nested or parent_id not in (None, ''):
            return super().list(request, *args, **kwargs)

        parent_queryset = self.filter_queryset(self.get_queryset()).filter(parent_id__isnull=True)
        parent_indicators = list(parent_queryset)
        parent_ids = [indicator.id for indicator in parent_indicators]
        child_indicators = list(
            self.get_queryset().filter(parent_id__in=parent_ids)
            .order_by('sort_no', 'id')
        )

        parent_data = self.get_serializer(parent_indicators, many=True).data
        child_data = self.get_serializer(child_indicators, many=True).data
        children_map = {}
        for child in child_data:
            children_map.setdefault(child['parent_id'], []).append(child)

        for parent in parent_data:
            parent['children'] = children_map.get(parent['id'], [])

        return Response({'message': '查询成功', 'data': parent_data})

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'message': '查询成功', 'data': serializer.data})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        output_serializer = self.get_serializer(serializer.instance)
        headers = self.get_success_headers(output_serializer.data)
        response = Response({'message': '创建成功', 'data': output_serializer.data}, status=status.HTTP_201_CREATED)
        for key, value in headers.items():
            response[key] = value
        return response

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        output_serializer = self.get_serializer(serializer.instance)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response({'message': '更新成功', 'data': output_serializer.data})

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if PerfIndicator.objects.filter(parent_id=instance.id).exists():
            raise ValidationError({'message': '当前指标存在下级指标，请先删除下级指标后再删除'})
        if PerfIndicatorRule.objects.filter(indicator_id=instance.id).exists():
            raise ValidationError({'message': '当前指标已被指标规则引用，请先删除关联规则后再删除'})
        self.perform_destroy(instance)
        return Response({'message': '删除成功', 'data': None})


# 指标规则管理
class PerfIndicatorRuleViewSet(viewsets.ModelViewSet):
    queryset = PerfIndicatorRule.objects.all().order_by('-indicator_id', '-rule_version', '-id')
    serializer_class = PerfIndicatorRuleSerializer
    permission_classes = [IsAdminUserLevel]

    def _attach_indicator_info(self, objects):
        rule_list = list(objects)
        if not rule_list:
            return rule_list

        indicator_ids = {rule.indicator_id for rule in rule_list if rule.indicator_id is not None}
        indicator_map = {
            item['id']: item
            for item in PerfIndicator.objects.filter(id__in=indicator_ids).values('id', 'indicator_code', 'indicator_name')
        }

        for rule in rule_list:
            indicator = indicator_map.get(rule.indicator_id)
            rule.indicator_code = indicator['indicator_code'] if indicator else None
            rule.indicator_name = indicator['indicator_name'] if indicator else None

        return rule_list

    def get_queryset(self):
        queryset = super().get_queryset()
        indicator_id = self.request.query_params.get('indicator_id')
        status_value = self.request.query_params.get('status')
        indicator_code = self.request.query_params.get('indicator_code')
        indicator_name = self.request.query_params.get('indicator_name')

        if indicator_code or indicator_name:
            indicator_queryset = PerfIndicator.objects.all()
            if indicator_code:
                indicator_queryset = indicator_queryset.filter(indicator_code__icontains=indicator_code)
            if indicator_name:
                indicator_queryset = indicator_queryset.filter(indicator_name__icontains=indicator_name)
            indicator_ids = indicator_queryset.values_list('id', flat=True)
            queryset = queryset.filter(indicator_id__in=indicator_ids)

        is_current = parse_bool_param(self.request.query_params.get('is_current'))

        if indicator_id not in (None, ''):
            queryset = queryset.filter(indicator_id=indicator_id)
        if status_value:
            queryset = queryset.filter(status=status_value)
        if is_current is not None:
            queryset = queryset.filter(is_current=is_current)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            self._attach_indicator_info(page)
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        rules = self._attach_indicator_info(queryset)
        serializer = self.get_serializer(rules, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        self._attach_indicator_info([instance])
        serializer = self.get_serializer(instance)
        return Response({'message': '查询成功', 'data': serializer.data})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        self._attach_indicator_info([serializer.instance])
        output_serializer = self.get_serializer(serializer.instance)
        headers = self.get_success_headers(output_serializer.data)
        response = Response({'message': '创建成功', 'data': output_serializer.data}, status=status.HTTP_201_CREATED)
        for key, value in headers.items():
            response[key] = value
        return response

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        self._attach_indicator_info([serializer.instance])
        output_serializer = self.get_serializer(serializer.instance)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response({'message': '更新成功', 'data': output_serializer.data})

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'message': '删除成功', 'data': None})


class PerfIndicatorDashboardView(APIView):
    """绩效指标仪表板视图"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        query_serializer = PerfIndicatorDashboardQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        data_dt = query_serializer.validated_data['data_dt']
        parent_indicator_id = query_serializer.validated_data['parent_indicator_id']
        org_id = (query_serializer.validated_data.get('org_id') or '').strip()

        # 如果没有传入 org_id，判断用户权限
        if not org_id:
            user = request.user
            org_ids = UserOrgRelation.objects.filter(user_id=user.id).values_list('org_id', flat=True)
            orgs_types = set(OrgUnit.objects.filter(
                status=OrgUnit.Status.NORMAL, 
                id__in=org_ids).values_list('org_type', flat=True))
            if orgs_types & {OrgUnit.OrgType.SUB_BRANCH, OrgUnit.OrgType.TEAM}:
                raise ValidationError({'message': '无权限访问', 'data': None})

        parent_indicator = PerfIndicator.objects.filter(
            id=parent_indicator_id, 
            status=PerfIndicator.Status.ENABLED,
        ).first()
        
        if parent_indicator is None:
            raise ValidationError({'parent_indicator_id': ['父指标不存在']})

        selected_org = None
        org_code = None
        if org_id:
            selected_org = OrgUnit.objects.filter(
                id=org_id, 
                status=OrgUnit.Status.NORMAL
            ).only('id', 'org_code', 'org_name').first()
            if selected_org is None:
                raise ValidationError({'org_id': ['机构不存在']})
            org_code = str(selected_org.org_code)

        leaf_indicators = list(
            PerfIndicator.objects.filter(parent_id=parent_indicator_id, status=PerfIndicator.Status.ENABLED)
            .order_by('sort_no', 'id')
            .only('id', 'indicator_code', 'indicator_name', 'parent_id', 
                'display_unit', 'decimal_places', 'sort_no')
        )

        start_dt = data_dt - timedelta(days=29)
        aggregated_rows = self._load_indicator_result_map(
            leaf_indicators=leaf_indicators,
            start_dt=start_dt,
            end_dt=data_dt,
            org_code=org_code,
        )
        indicator_org_snapshot = {}
        if not org_code:
            indicator_org_snapshot = self._load_indicator_org_snapshot(
                leaf_indicators=leaf_indicators,
                data_dt=data_dt,
            )

        indicator_payload = [
            self._build_indicator_dashboard_item(indicator, data_dt, start_dt, aggregated_rows, indicator_org_snapshot)
            for indicator in leaf_indicators
        ]

        return Response(
            {
                'message': '查询成功',
                'data': indicator_payload
            }
        )

    def _load_indicator_result_map(self, leaf_indicators, start_dt, end_dt, org_code=None):
        if not leaf_indicators:
            return {}

        indicator_ids = [indicator.id for indicator in leaf_indicators]
        queryset = PerfIndicatorResult.objects.filter(
            indicator_id__in=indicator_ids,
            data_dt__range=(start_dt, end_dt),
            calc_status=PerfIndicatorResult.CalcStatus.SUCCESS,
        )

        if org_code:
            current_rules = {
                rule['indicator_id']: self._build_result_org_id(org_code, rule['org_prefix'])
                for rule in PerfIndicatorRule.objects.filter(indicator_id__in=indicator_ids, is_current=True)
                .values('indicator_id', 'org_prefix')
            }
            filtered_pairs = {
                indicator.id: current_rules.get(indicator.id, org_code)
                for indicator in leaf_indicators
            }
            condition = Q()
            for indicator_id, result_org_id in filtered_pairs.items():
                condition |= Q(indicator_id=indicator_id, org_id=result_org_id)
            queryset = queryset.filter(condition)

        rows = queryset.values('indicator_id', 'data_dt').annotate(
            day_avg=Sum('metric_value'),
            point_in_time=Sum('metric_value_2'),
        )
        return {
            (row['indicator_id'], row['data_dt']): {
                'day_avg': row['day_avg'],
                'point_in_time': row['point_in_time'],
            }
            for row in rows
        }

    def _load_indicator_org_snapshot(self, leaf_indicators, data_dt):
        if not leaf_indicators:
            return {}

        indicator_ids = [indicator.id for indicator in leaf_indicators]
        rows = list(
            PerfIndicatorResult.objects.filter(
                indicator_id__in=indicator_ids,
                data_dt=data_dt,
                calc_status=PerfIndicatorResult.CalcStatus.SUCCESS,
            )
            .values('indicator_id', 'org_id')
            .annotate(
                day_avg=Sum('metric_value'),
                point_in_time=Sum('metric_value_2'),
            )
        )

        org_ids = {str(row['org_id'])[-8:] for row in rows if row['org_id']}
        org_name_map = {
            str(item['org_code']): item['org_name']
            for item in OrgUnit.objects.filter(org_code__in=org_ids, status=OrgUnit.Status.NORMAL)
            .values('org_code', 'org_name')
        }

        indicator_map = {indicator.id: [] for indicator in leaf_indicators}
        for row in rows:
            org_name = org_name_map.get(str(row['org_id'])[-8:])
            if not org_name:
                continue
            indicator_map.setdefault(row['indicator_id'], []).append(
                {
                    'org_id': row['org_id'],
                    'org_name': org_name,
                    'day_avg': self._to_number(row['day_avg']),
                    'point_in_time': self._to_number(row['point_in_time']),
                }
            )

        result = {}
        for indicator_id, org_values in indicator_map.items():
            day_avg_org_values = sorted(
                [
                    {
                        'org_id': item['org_id'],
                        'org_name': item['org_name'],
                        'day_avg': item['day_avg'],
                    }
                    for item in org_values
                ],
                key=lambda item: (item['day_avg'] is None, item['day_avg'] or 0)
            )
            point_in_time_org_values = sorted(
                [
                    {
                        'org_id': item['org_id'],
                        'org_name': item['org_name'],
                        'point_in_time': item['point_in_time'],
                    }
                    for item in org_values
                ],
                key=lambda item: (item['point_in_time'] is None, item['point_in_time'] or 0)
            )
            result[indicator_id] = {
                'day_avg_org_values': day_avg_org_values,
                'point_in_time_org_values': point_in_time_org_values,
            }
        
        return result

    def _build_indicator_dashboard_item(self, indicator, data_dt, start_dt, aggregated_rows, indicator_org_snapshot):
        current_row = aggregated_rows.get((indicator.id, data_dt), {})
        previous_row = aggregated_rows.get((indicator.id, data_dt - timedelta(days=1)), {})

        day_avg = current_row.get('day_avg')
        day_avg_dod = self._build_ratio(day_avg, previous_row.get('day_avg'))
        day_avg_dod_direction = self._build_ratio_direction(day_avg_dod)
        
        point_in_time = current_row.get('point_in_time')
        point_in_time_dod = self._build_ratio(point_in_time, previous_row.get('point_in_time'))
        point_in_time_dod_direction = self._build_ratio_direction(point_in_time_dod)

        return {
            'indicator_name': indicator.indicator_name,
            'day_avg': self._to_number(day_avg),
            'day_avg_dod': day_avg_dod,
            'day_avg_dod_direction': day_avg_dod_direction,
            'point_in_time': self._to_number(point_in_time),
            'point_in_time_dod': point_in_time_dod,
            'point_in_time_dod_direction': point_in_time_dod_direction,
            'completion_rate': None,
            'completion_rate_ratio': None,
            'completion_rate_direction': None,
            'org_values': indicator_org_snapshot.get(indicator.id, []),
            'day_avg_series': self._build_series(indicator.id, start_dt, data_dt, aggregated_rows, 'day_avg'),
            'point_in_time_series': self._build_series(
                indicator.id,
                start_dt,
                data_dt,
                aggregated_rows,
                'point_in_time',
            ),
        }

    def _build_series(self, indicator_id, start_dt, end_dt, aggregated_rows, field_name):
        series = []
        has_value = False
        current_dt = start_dt

        while current_dt <= end_dt:
            value = aggregated_rows.get((indicator_id, current_dt), {}).get(field_name)
            if value is not None:
                has_value = True
            series.append(
                {
                    'data_dt': current_dt.isoformat(),
                    'value': self._to_number(value),
                }
            )
            current_dt += timedelta(days=1)

        return series if has_value else []

    def _build_ratio(self, current_value, previous_value):
        if current_value is None or previous_value is None:
            return None

        previous_decimal = Decimal(str(previous_value))
        if previous_decimal == 0:
            return None

        current_decimal = Decimal(str(current_value))
        ratio = ((current_decimal - previous_decimal) / previous_decimal) * Decimal('100')
        return float(ratio.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))

    def _build_ratio_direction(self, ratio_value):
        if ratio_value is None:
            return None
        if ratio_value > 0:
            return 'up'
        if ratio_value < 0:
            return 'down'
        return 'flat'

    def _to_number(self, value):
        if value is None:
            return None
        # todo: 先默认除10000后进行展示，后续需要根据指标配置来决定是否除10000
        return float(
            (Decimal(str(value)) / Decimal('10000')).quantize(
                Decimal('0.00'),
                rounding=ROUND_HALF_UP
            )
        )

    def _build_result_org_id(self, org_code, org_prefix):
        return f'{org_prefix}{org_code}' if org_prefix else org_code


# 机构选项
class OrgOptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        org_ids = UserOrgRelation.objects.filter(user_id=user.id).values_list('org_id', flat=True)
        orgs_types = set(OrgUnit.objects.filter(
            status=OrgUnit.Status.NORMAL, 
            id__in=org_ids).values_list('org_type', flat=True))
        if orgs_types & {OrgUnit.OrgType.SUB_BRANCH, OrgUnit.OrgType.TEAM}:
            orgs = list(
                OrgUnit.objects.filter(status=OrgUnit.Status.NORMAL, id__in=org_ids)
                .order_by('display_order', 'id')
                .values('id', 'org_name')
            )
        else:
            orgs = list(
                OrgUnit.objects.filter(status=OrgUnit.Status.NORMAL)
                .order_by('display_order', 'id')
                .values('id', 'org_name')
            )
        return Response({'message': '查询成功', 'data': orgs})


# 父指标选项
class ParentIndicatorOptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        indicators = list(
            PerfIndicator.objects.filter(status=PerfIndicator.Status.ENABLED, parent_id__isnull=True)
            .order_by('sort_no')
            .values('id', 'indicator_name')
        )
        return Response({'message': '查询成功', 'data': indicators})


# 指标选项
class IndicatorOptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        indicator_name = (request.query_params.get('indicator_name') or '').strip()
        queryset = PerfIndicator.objects.filter(status=PerfIndicator.Status.ENABLED).order_by('sort_no', 'id')

        if indicator_name:
            queryset = queryset.filter(indicator_name__icontains=indicator_name)

        indicators = list(queryset.values('id', 'indicator_name'))
        return Response({'message': '查询成功', 'data': indicators})


# 总行下发数据导入日志
class DataImportLogView(APIView):
    permission_classes = [IsAdminUserLevel]

    def get(self, request):
        query_serializer = DataImportLogQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        data_dt = resolve_import_date(query_serializer.validated_data.get('data_dt'))
        queryset = DataImportLog.objects.filter(data_date=data_dt).order_by('file_name', '-updated_at', '-id')
        result_log = ResultImportLog.objects.filter(data_date=data_dt).first()
        post_profit_indicator_logs = list_post_profit_indicator_logs(data_dt)
        dependency_tables = list_result_import_dependencies()
        missing_tables = get_missing_dependency_tables(data_dt)

        return Response(
            {
                'message': '查询成功',
                'data': {
                    'data_dt': data_dt.isoformat(),
                    'summary': {
                        'result_import_log':[ResultImportLogSerializer(result_log).data if result_log else None],
                        'post_profit_indicator_logs': ResultImportIndicatorLogPostProfitSerializer(
                            post_profit_indicator_logs,
                            many=True,
                        ).data,
                        'dependency_ready': len(missing_tables) == 0 if dependency_tables else False,
                        'dependency_tables': dependency_tables,
                        'missing_dependency_tables': missing_tables,
                    },
                    'file_logs': DataImportLogSerializer(queryset, many=True).data,
                },
            }
        )


# 总行下发数据导入触发
class HeadOfficeImportTriggerView(APIView):
    permission_classes = [IsAdminUserLevel]

    def post(self, request):
        data_dt = parse_optional_date_param(request.data.get('data_dt'))
        resolved_data_dt = resolve_import_date(data_dt).isoformat()
        async_result = run_head_office_import.delay(data_dt=resolved_data_dt)
        return Response(
            {
                'message': '总行下发数据导入任务已提交',
                'data': {
                    'task_id': async_result.id,
                    'data_dt': resolved_data_dt,
                },
            },
            status=status.HTTP_202_ACCEPTED,
        )


# 结果数据导入触发
class ResultImportTriggerView(APIView):
    permission_classes = [IsAdminUserLevel]

    def post(self, request):
        data_dt = parse_optional_date_param(request.data.get('data_dt'))
        resolved_data_dt = resolve_import_date(data_dt).isoformat()
        force = parse_bool_param(request.data.get('force'), default=False)
        if request.data.get('force') not in (None, '') and force is None:
            raise ValidationError({'force': ['force参数格式错误，应为true/false']})

        async_result = run_datahub_result_import.delay(data_dt=resolved_data_dt, force=force)
        return Response(
            {
                'message': '结果表导入任务已提交',
                'data': {
                    'task_id': async_result.id,
                    'data_dt': resolved_data_dt,
                    'force': force,
                },
            },
            status=status.HTTP_202_ACCEPTED,
        )


class ResultImportPostProfitTriggerView(APIView):
    permission_classes = [IsAdminUserLevel]

    def post(self, request):
        data_dt = parse_optional_date_param(request.data.get('data_dt'))
        resolved_data_dt = resolve_import_date(data_dt).isoformat()
        force = parse_bool_param(request.data.get('force'), default=False)
        if request.data.get('force') not in (None, '') and force is None:
            raise ValidationError({'force': ['force参数格式错误，应为true/false']})

        async_result = run_datahub_post_profit_result_import.delay(data_dt=resolved_data_dt, force=force)
        return Response(
            {
                'message': '分润后结果表导入任务已提交',
                'data': {
                    'task_id': async_result.id,
                    'data_dt': resolved_data_dt,
                    'force': force,
                },
            },
            status=status.HTTP_202_ACCEPTED,
        )


# 手动触发数据备份
class AutoLoadDataBackupTriggerView(APIView):
    permission_classes = [IsAdminUserLevel]

    def post(self, request):
        data_dt = resolve_backup_date(parse_optional_date_param(request.data.get('data_dt')))
        async_result = run_auto_load_data_backup_task.delay(data_dt=data_dt.isoformat())
        return Response(
            {
                'message': '数据备份任务已提交',
                'data': {
                    'task_id': async_result.id,
                    'data_dt': data_dt.isoformat(),
                },
            },
            status=status.HTTP_202_ACCEPTED,
        )
