import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.conf import settings
from django.db import close_old_connections
from celery import shared_task

from .models import ResultImportIndicatorLogPostProfit, ResultImportLog
from .services.data_backup import run_auto_load_data_backup
from .services.head_office_import import run_import
from .services.import_pipeline import (
    get_result_import_log,
    has_running_post_profit_indicator_logs,
    is_result_import_ready,
    list_result_import_dependencies,
    list_successful_post_profit_indicator_ids,
    mark_post_profit_indicator_status,
    mark_result_import_status,
    resolve_import_date,
)
from .services.indicator_calculation import execute_rule, list_active_rule_ids
from .services.post_profit_indicator_calculation import (
    execute_post_profit_rule_batch,
    list_active_post_profit_rules,
)


logger = logging.getLogger(__name__)


@shared_task(name='datahub.run_auto_load_data_backup')
def run_auto_load_data_backup_task(data_dt=None):
    summary = run_auto_load_data_backup(data_dt=data_dt)
    logger.info('自动加载目录备份任务完成 data_dt=%s summary=%s', summary['data_date'], summary)
    return summary


# 调度所有指标规则(暂未使用)
@shared_task(name='datahub.schedule_all_indicator_rules')
def schedule_all_indicator_rules(data_dt=None, day_count=None, org_id=None):
    logger.info('开始调度指标规则 data_dt=%s day_count=%s org_id=%s', data_dt, day_count, org_id)
    rule_ids = list_active_rule_ids()
    dispatched = []
    failed = []

    for rule_id in rule_ids:
        try:
            async_result = execute_indicator_rule.delay(
                rule_id=rule_id,
                data_dt=data_dt,
                day_count=day_count,
                org_id=org_id,
            )
            dispatched.append({'rule_id': rule_id, 'task_id': async_result.id})
        except Exception as exc:
            logger.exception('dispatch indicator rule failed rule_id=%s', rule_id)
            failed.append({'rule_id': rule_id, 'error': str(exc)})

    result = {
        'scheduled_count': len(dispatched),
        'failed_count': len(failed),
        'dispatched': dispatched,
        'failed': failed,
    }
    logger.info('指标规则调度完成 data_dt=%s scheduled=%s failed=%s', data_dt, len(dispatched), len(failed))
    return result


# 执行指标规则(暂未使用)
@shared_task(name='datahub.execute_indicator_rule')
def execute_indicator_rule(rule_id, data_dt=None, day_count=None, org_id=None):
    return execute_rule(
        rule_id=rule_id,
        data_dt=data_dt,
        day_count=day_count,
        org_id=org_id,
    )


# 执行全部指标规则
def execute_all_indicator_rules(data_dt=None, day_count=None, org_id=None):
    logger.info('开始执行全部指标规则 data_dt=%s day_count=%s org_id=%s', data_dt, day_count, org_id)
    rule_ids = list_active_rule_ids()
    succeeded = []
    failed = []

    if not rule_ids:
        return {
            'rule_count': 0,
            'success_count': 0,
            'failed_count': 0,
            'succeeded': [],
            'failed': [],
        }

    max_workers = max(1, min(getattr(settings, 'DATAHUB_RESULT_IMPORT_MAX_WORKERS', 4), len(rule_ids)))
    logger.info('结果表规则执行并发数 workers=%s rule_count=%s', max_workers, len(rule_ids))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(_execute_rule_threadsafe, rule_id, data_dt, day_count, org_id): rule_id
            for rule_id in rule_ids
        }

        for future in as_completed(future_map):
            rule_id = future_map[future]
            try:
                result = future.result()
                succeeded.append({'rule_id': rule_id, 'result': result})
            except Exception as exc:
                logger.exception('execute indicator rule failed rule_id=%s data_dt=%s', rule_id, data_dt)
                failed.append({'rule_id': rule_id, 'error': str(exc)})

    summary = {
        'rule_count': len(rule_ids),
        'success_count': len(succeeded),
        'failed_count': len(failed),
        'succeeded': succeeded,
        'failed': failed,
    }
    logger.info(
        '全部指标规则执行完成 data_dt=%s total=%s success=%s failed=%s',
        data_dt,
        len(rule_ids),
        len(succeeded),
        len(failed),
    )
    return summary


# 线程安全的执行指标规则
def _execute_rule_threadsafe(rule_id, data_dt=None, day_count=None, org_id=None):
    close_old_connections()
    try:
        return execute_rule(
            rule_id=rule_id,
            data_dt=data_dt,
            day_count=day_count,
            org_id=org_id,
        )
    finally:
        close_old_connections()


def execute_post_profit_indicator_rules(import_date, rules, org_id=None):
    succeeded = []
    failed = []

    if not rules:
        return {
            'rule_count': 0,
            'success_count': 0,
            'failed_count': 0,
            'succeeded': [],
            'failed': [],
        }

    max_workers = max(1, min(getattr(settings, 'DATAHUB_RESULT_IMPORT_MAX_WORKERS', 4), len(rules)))
    logger.info('分润后结果表规则执行并发数 workers=%s rule_count=%s', max_workers, len(rules))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(
                _execute_post_profit_rule_threadsafe,
                import_date,
                rule['id'],
                rule['indicator_id'],
                org_id,
            ): rule
            for rule in rules
        }

        for future in as_completed(future_map):
            rule = future_map[future]
            try:
                result = future.result()
                succeeded.append({'rule_id': rule['id'], 'indicator_id': rule['indicator_id'], 'result': result})
            except Exception as exc:
                logger.exception(
                    'execute post profit indicator rule failed rule_id=%s indicator_id=%s data_dt=%s',
                    rule['id'],
                    rule['indicator_id'],
                    import_date,
                )
                failed.append({'rule_id': rule['id'], 'indicator_id': rule['indicator_id'], 'error': str(exc)})

    return {
        'rule_count': len(rules),
        'success_count': len(succeeded),
        'failed_count': len(failed),
        'succeeded': succeeded,
        'failed': failed,
    }


def _execute_post_profit_rule_threadsafe(import_date, rule_id, indicator_id, org_id=None):
    close_old_connections()
    mark_post_profit_indicator_status(
        import_date,
        indicator_id,
        status=ResultImportIndicatorLogPostProfit.Status.RUNNING,
        message='分润后结果表导入执行中',
        rule_id=rule_id,
    )
    try:
        result = execute_post_profit_rule_batch(
            rule_id=rule_id,
            data_dt=import_date,
            org_id=org_id,
        )
        mark_post_profit_indicator_status(
            import_date,
            indicator_id,
            status=ResultImportIndicatorLogPostProfit.Status.SUCCESS,
            message=f"分润后结果表导入完成，共执行 {result['total_days']} 天",
            rule_id=rule_id,
        )
        return result
    except Exception as exc:
        mark_post_profit_indicator_status(
            import_date,
            indicator_id,
            status=ResultImportIndicatorLogPostProfit.Status.FAILED,
            message=str(exc),
            rule_id=rule_id,
        )
        raise
    finally:
        close_old_connections()


# 总行下发数据导入
@shared_task(name='datahub.run_head_office_import')
def run_head_office_import(data_dt=None):
    resolved_date = resolve_import_date(data_dt)
    summary = run_import(date_str=resolved_date.isoformat())
    logger.info('总行下发数据导入完成 data_dt=%s summary=%s', resolved_date, summary)
    return {
        'status': summary['status'],
        'data_date': resolved_date.isoformat(),
        'summary': summary,
    }


# 数据中心结果表导入
@shared_task(name='datahub.run_datahub_result_import')
def run_datahub_result_import(data_dt=None, org_id=None, force=False):
    resolved_date = resolve_import_date(data_dt)
    existing_log = get_result_import_log(resolved_date)
    day_count = resolved_date.timetuple().tm_yday

    if existing_log and existing_log.status == ResultImportLog.Status.RUNNING:
        message = f'结果表导入任务正在执行，跳过重复触发 data_dt={resolved_date.isoformat()}'
        logger.info(message)
        return {
            'status': 'skipped',
            'data_date': resolved_date.isoformat(),
            'message': message,
        }

    if existing_log and existing_log.status == ResultImportLog.Status.SUCCESS and not force:
        message = f'结果表数据已完成导入，跳过重复执行 data_dt={resolved_date.isoformat()}'
        logger.info(message)
        return {
            'status': 'skipped',
            'data_date': resolved_date.isoformat(),
            'message': message,
        }

    dependency_tables = list_result_import_dependencies()
    if not dependency_tables:
        message = '未配置结果表导入依赖表'
        mark_result_import_status(resolved_date, ResultImportLog.Status.FAILED, message)
        logger.warning('结果表导入跳过 data_dt=%s reason=%s', resolved_date, message)
        return {
            'status': 'failed',
            'data_date': resolved_date.isoformat(),
            'message': message,
        }

    ready, missing_tables = is_result_import_ready(resolved_date)
    if not ready and not force:
        message = f"结果表导入依赖表尚未全部导入成功: {', '.join(missing_tables)}"
        mark_result_import_status(resolved_date, ResultImportLog.Status.PENDING, message)
        logger.info('结果表导入暂不执行 data_dt=%s missing=%s', resolved_date, missing_tables)
        return {
            'status': 'pending',
            'data_date': resolved_date.isoformat(),
            'message': message,
            'missing_tables': missing_tables,
        }

    mark_result_import_status(
        resolved_date,
        ResultImportLog.Status.RUNNING,
        '结果表导入执行中' if not force else '结果表导入强制执行中',
    )
    try:
        result = execute_all_indicator_rules(
            data_dt=resolved_date.isoformat(),
            day_count=day_count,
            org_id=org_id,
        )
        if result['failed_count']:
            message = f"结果表导入失败 {result['failed_count']} 条规则"
            mark_result_import_status(resolved_date, ResultImportLog.Status.FAILED, message)
            raise RuntimeError(message)

        message = f"结果表导入完成，共执行 {result['success_count']} 条规则"
        mark_result_import_status(resolved_date, ResultImportLog.Status.SUCCESS, message)
        return {
            'status': 'success',
            'data_date': resolved_date.isoformat(),
            'result': result,
        }
    except Exception as exc:
        mark_result_import_status(resolved_date, ResultImportLog.Status.FAILED, str(exc))
        logger.exception('结果表导入任务失败 data_dt=%s', resolved_date)
        raise


@shared_task(name='datahub.run_datahub_post_profit_result_import')
def run_datahub_post_profit_result_import(data_dt=None, org_id=None, force=False):
    resolved_date = resolve_import_date(data_dt)
    active_rules = list_active_post_profit_rules()

    if has_running_post_profit_indicator_logs(resolved_date):
        message = f'分润后结果表导入任务正在执行，跳过重复触发 data_dt={resolved_date.isoformat()}'
        logger.info(message)
        return {
            'status': 'skipped',
            'data_date': resolved_date.isoformat(),
            'message': message,
        }

    active_indicator_ids = {rule['indicator_id'] for rule in active_rules}
    succeeded_indicator_ids = set() if force else set(list_successful_post_profit_indicator_ids(resolved_date))

    if active_indicator_ids and active_indicator_ids.issubset(succeeded_indicator_ids):
        message = f'分润后结果表数据已完成导入，跳过重复执行 data_dt={resolved_date.isoformat()}'
        logger.info(message)
        return {
            'status': 'skipped',
            'data_date': resolved_date.isoformat(),
            'message': message,
        }

    pending_rules = active_rules if force else [
        rule for rule in active_rules
        if rule['indicator_id'] not in succeeded_indicator_ids
    ]
    if not pending_rules:
        message = f'分润后结果表指标已全部导入成功，跳过执行 data_dt={resolved_date.isoformat()}'
        logger.info(message)
        return {
            'status': 'skipped',
            'data_date': resolved_date.isoformat(),
            'message': message,
        }
    try:
        result = execute_post_profit_indicator_rules(
            import_date=resolved_date,
            rules=pending_rules,
            org_id=org_id,
        )
        latest_success_ids = set(list_successful_post_profit_indicator_ids(resolved_date))
        failed_indicator_ids = sorted(active_indicator_ids - latest_success_ids)
        if result['failed_count'] or failed_indicator_ids:
            message = (
                f"分润后结果表导入失败 {result['failed_count']} 条规则，"
                f"未成功指标: {', '.join(map(str, failed_indicator_ids))}"
            )
            raise RuntimeError(message)

        message = f"分润后结果表导入完成，共执行 {result['success_count']} 条规则"
        return {
            'status': 'success',
            'data_date': resolved_date.isoformat(),
            'message': message,
            'result': result,
        }
    except Exception:
        logger.exception('分润后结果表导入任务失败 data_dt=%s', resolved_date)
        raise
