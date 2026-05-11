import logging
from datetime import date
from string import Formatter

from django.conf import settings
from django.db import connection, transaction
from django.utils import timezone

from apps.datahub.models import PerfIndicatorResult, PerfIndicatorRule


logger = logging.getLogger(__name__)


class IndicatorCalculationError(Exception):
    """指标计算业务异常。"""


def build_execution_params(rule, data_dt=None, day_count=None, org_id=None):
    params = {}

    if rule.need_date_param:
        resolved_data_dt = data_dt or timezone.localdate()
        if isinstance(resolved_data_dt, str):
            try:
                resolved_data_dt = date.fromisoformat(resolved_data_dt)
            except ValueError as exc:
                raise IndicatorCalculationError('data_dt 必须是 YYYY-MM-DD 格式') from exc
        if not isinstance(resolved_data_dt, date):
            raise IndicatorCalculationError('data_dt 必须是 YYYY-MM-DD 或 date 类型')
        params['data_dt'] = resolved_data_dt.isoformat()

    if rule.need_day_count_param:
        try:
            resolved_day_count = settings.DATAHUB_DEFAULT_DAY_COUNT if day_count is None else int(day_count)
        except (TypeError, ValueError) as exc:
            raise IndicatorCalculationError('day_count 必须是整数') from exc
        params['day_count'] = resolved_day_count

    # org_id 对多数规则都是可选过滤，传空字符串表示不限制机构
    params['org_id'] = '' if org_id in (None, '') else str(org_id)
    return params


def render_sql_template(sql_template, params):
    if not sql_template:
        return ''

    placeholder_names = {
        field_name
        for _, field_name, _, _ in Formatter().parse(sql_template)
        if field_name
    }
    missing_names = sorted(name for name in placeholder_names if name not in params)
    if missing_names:
        raise IndicatorCalculationError(f'SQL 模板缺少参数: {", ".join(missing_names)}')

    try:
        return sql_template.format(**params)
    except KeyError as exc:
        raise IndicatorCalculationError(f'SQL 模板缺少参数: {exc.args[0]}') from exc


def list_active_rule_ids():
    return list(
        PerfIndicatorRule.objects.filter(status=PerfIndicatorRule.Status.ENABLED, is_current=True)
        .order_by('indicator_id', 'rule_version', 'id')
        .values_list('id', flat=True)
    )


def get_rule(rule_id):
    try:
        return PerfIndicatorRule.objects.get(id=rule_id)
    except PerfIndicatorRule.DoesNotExist as exc:
        raise IndicatorCalculationError(f'指标规则不存在: {rule_id}') from exc


def execute_rule(rule_id, data_dt=None, day_count=None, org_id=None):
    rule = get_rule(rule_id)
    params = build_execution_params(rule, data_dt=data_dt, day_count=day_count, org_id=org_id)
    source_sql = render_sql_template(rule.sql_template, params)
    target_sql = render_sql_template(rule.target_sql_template, params) if rule.target_sql_template else ''

    if not settings.DATAHUB_SQL_EXECUTION_ENABLED:
        logger.info(
            'indicator_rule execution skipped rule_id=%s indicator_id=%s source_sql=%s target_sql=%s',
            rule.id,
            rule.indicator_id,
            source_sql,
            target_sql,
        )
        return {
            'rule_id': rule.id,
            'indicator_id': rule.indicator_id,
            'status': 'skipped',
            'reason': 'SQL execution disabled',
            'params': params,
            'source_sql': source_sql,
            'target_sql': target_sql,
        }

    source_rows = execute_sql(source_sql)
    target_rows = execute_sql(target_sql) if target_sql else []
    written_count = persist_rule_results(rule, params, source_rows, target_rows)
    return {
        'rule_id': rule.id,
        'indicator_id': rule.indicator_id,
        'status': 'success',
        'params': params,
        'source_row_count': len(source_rows),
        'target_row_count': len(target_rows),
        'written_count': written_count,
    }


def execute_sql(sql):
    with connection.cursor() as cursor:
        cursor.execute(sql)
        columns = [column[0] for column in cursor.description or []]
        rows = cursor.fetchall() if columns else []
    return [dict(zip(columns, row)) for row in rows]


def persist_rule_results(rule, params, source_rows, target_rows):
    if not source_rows:
        return 0

    target_by_org = {str(row.get('org_id', '')): row for row in target_rows}
    written_count = 0

    with transaction.atomic():
        for row in source_rows:
            org_id = str(row.get('org_id', params['org_id']))
            if not org_id:
                raise IndicatorCalculationError(f'指标规则 {rule.id} 缺少 org_id 输出字段')

            target_row = target_by_org.get(org_id, {})
            defaults = build_result_defaults(row, target_row)
            PerfIndicatorResult.objects.update_or_create(
                data_dt=date.fromisoformat(params['data_dt']),
                indicator_id=rule.indicator_id,
                org_id=org_id,
                defaults=defaults,
            )
            written_count += 1

    return written_count


def build_result_defaults(source_row, target_row):
    merged = {**target_row, **source_row}
    return {
        'metric_value': merged.get('metric_value'),
        'metric_value_2': merged.get('metric_value_2'),
        'metric_value_3': merged.get('metric_value_3'),
        'target_value': merged.get('target_value'),
        'completion_rate': merged.get('completion_rate'),
        'rank_no': merged.get('rank_no'),
        'is_topn': bool(merged.get('is_topn', False)),
        'calc_status': merged.get('calc_status', PerfIndicatorResult.CalcStatus.SUCCESS),
        'error_msg': merged.get('error_msg'),
        'extra_json': merged.get('extra_json'),
    }
