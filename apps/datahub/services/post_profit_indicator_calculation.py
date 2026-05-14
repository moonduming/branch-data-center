import logging
from datetime import date, timedelta

from django.conf import settings
from django.db import InterfaceError, OperationalError, close_old_connections

from apps.datahub.models import PerfIndicatorResultPostProfit, PerfIndicatorRulePostProfit
from apps.datahub.services.indicator_calculation import (
    IndicatorCalculationError,
    build_execution_params,
    build_result_defaults,
    execute_sql,
    render_sql_template,
)


logger = logging.getLogger(__name__)


POST_PROFIT_WINDOW_DAYS = 30


def list_active_post_profit_rules():
    return list(
        PerfIndicatorRulePostProfit.objects.filter(
            status=PerfIndicatorRulePostProfit.Status.ENABLED,
            is_current=True,
        )
        .order_by('indicator_id', 'rule_version', 'id')
        .values('id', 'indicator_id')
    )


def get_post_profit_rule(rule_id):
    try:
        return PerfIndicatorRulePostProfit.objects.get(id=rule_id)
    except PerfIndicatorRulePostProfit.DoesNotExist as exc:
        raise IndicatorCalculationError(f'分润指标规则不存在: {rule_id}') from exc


def build_post_profit_window_dates(data_dt, window_days=POST_PROFIT_WINDOW_DAYS):
    if isinstance(data_dt, str):
        data_dt = date.fromisoformat(data_dt)
    if not isinstance(data_dt, date):
        raise IndicatorCalculationError('data_dt 必须是 YYYY-MM-DD 或 date 类型')
    if window_days <= 0:
        raise IndicatorCalculationError('window_days 必须大于 0')

    start_date = data_dt - timedelta(days=window_days - 1)
    return [start_date + timedelta(days=offset) for offset in range(window_days)]


def execute_post_profit_rule_batch(rule_id, data_dt=None, org_id=None, window_days=POST_PROFIT_WINDOW_DAYS):
    rule = get_post_profit_rule(rule_id)
    execution_dates = build_post_profit_window_dates(data_dt, window_days=window_days)
    try:
        return _execute_post_profit_rule_batch_once(rule, execution_dates, org_id=org_id)
    except (OperationalError, InterfaceError) as exc:
        logger.warning(
            'post profit indicator batch retry after db connection issue rule_id=%s indicator_id=%s error=%s',
            rule.id,
            rule.indicator_id,
            exc,
        )
        close_old_connections()
        return _execute_post_profit_rule_batch_once(rule, execution_dates, org_id=org_id)


def _execute_post_profit_rule_batch_once(rule, execution_dates, org_id=None):
    day_results = []
    total_written_count = 0

    close_old_connections()

    for current_date in execution_dates:
        day_result = execute_post_profit_rule_for_date(
            rule=rule,
            data_dt=current_date,
            day_count=current_date.timetuple().tm_yday,
            org_id=org_id,
        )
        day_results.append(day_result)
        total_written_count += day_result['written_count']

    close_old_connections()
    return {
        'rule_id': rule.id,
        'indicator_id': rule.indicator_id,
        'status': 'success',
        'window_start_date': execution_dates[0].isoformat(),
        'window_end_date': execution_dates[-1].isoformat(),
        'total_days': len(execution_dates),
        'written_count': total_written_count,
        'day_results': day_results,
    }


def execute_post_profit_rule_for_date(rule, data_dt=None, day_count=None, org_id=None):
    params = build_execution_params(rule, data_dt=data_dt, day_count=day_count, org_id=org_id)
    daily_avg_sql = render_sql_template(rule.daily_avg_sql_template, params) if rule.daily_avg_sql_template else ''
    point_sql = render_sql_template(rule.point_sql_template, params) if rule.point_sql_template else ''

    if not settings.DATAHUB_SQL_EXECUTION_ENABLED:
        logger.info(
            'post profit indicator_rule execution skipped rule_id=%s indicator_id=%s daily_avg_sql=%s point_sql=%s',
            rule.id,
            rule.indicator_id,
            daily_avg_sql,
            point_sql,
        )
        return {
            'rule_id': rule.id,
            'indicator_id': rule.indicator_id,
            'data_dt': params.get('data_dt'),
            'status': 'skipped',
            'reason': 'SQL execution disabled',
            'params': params,
            'daily_avg_sql': daily_avg_sql,
            'point_sql': point_sql,
            'written_count': 0,
        }

    daily_avg_rows = execute_sql(daily_avg_sql) if daily_avg_sql else []
    point_rows = execute_sql(point_sql) if point_sql else []
    written_count = persist_post_profit_rule_results(rule, params, daily_avg_rows, point_rows)
    return {
        'rule_id': rule.id,
        'indicator_id': rule.indicator_id,
        'data_dt': params.get('data_dt'),
        'status': 'success',
        'params': params,
        'daily_avg_row_count': len(daily_avg_rows),
        'point_row_count': len(point_rows),
        'written_count': written_count,
    }


def persist_post_profit_rule_results(rule, params, daily_avg_rows, point_rows):
    daily_avg_by_key = {
        result_key: row
        for row in daily_avg_rows
        for result_key in [build_post_profit_result_key(row)]
        if result_key
    }
    point_by_key = {
        result_key: row
        for row in point_rows
        for result_key in [build_post_profit_result_key(row)]
        if result_key
    }
    all_keys = sorted(set(daily_avg_by_key) | set(point_by_key))

    if not all_keys:
        return 0

    written_count = 0
    for org_id, employee_no in all_keys:
        if not org_id:
            raise IndicatorCalculationError(f'分润指标规则 {rule.id} 缺少 org_id 输出字段')
        if not employee_no:
            raise IndicatorCalculationError(f'分润指标规则 {rule.id} 缺少 employee_no 输出字段')

        defaults = build_result_defaults(
            daily_avg_by_key.get((org_id, employee_no), {}),
            point_by_key.get((org_id, employee_no), {}),
        )
        defaults['employee_name'] = (
            point_by_key.get((org_id, employee_no), {}).get('employee_name')
            or daily_avg_by_key.get((org_id, employee_no), {}).get('employee_name')
        )
        PerfIndicatorResultPostProfit.objects.update_or_create(
            data_dt=date.fromisoformat(params['data_dt']),
            indicator_id=rule.indicator_id,
            org_id=org_id,
            employee_no=employee_no,
            defaults=defaults,
        )
        written_count += 1

    return written_count


def build_post_profit_result_key(row):
    org_id = str(row.get('org_id', '') or '').strip()
    employee_no = str(row.get('employee_no', '') or '').strip()
    if not org_id or not employee_no:
        return None
    return org_id, employee_no
