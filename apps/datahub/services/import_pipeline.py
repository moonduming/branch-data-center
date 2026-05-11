import os
from datetime import date, timedelta

from django.conf import settings
from django.utils import timezone

from apps.datahub.models import (
    DataImportLog,
    ResultImportDependency,
    ResultImportIndicatorLogPostProfit,
    ResultImportLog,
)


# 解析导入日期
def resolve_import_date(data_dt=None):
    if data_dt in (None, ''):
        day_offset = int(
            os.getenv(
                'HEAD_OFFICE_IMPORT_DAY_OFFSET',
                str(getattr(settings, 'HEAD_OFFICE_IMPORT_DAY_OFFSET', 1)),
            )
        )
        return timezone.localdate() - timedelta(days=day_offset)

    if isinstance(data_dt, date):
        return data_dt

    if isinstance(data_dt, str):
        return date.fromisoformat(data_dt)

    raise ValueError('data_dt 必须是 YYYY-MM-DD、date 或空值')


# 列出成功导入的文件
def list_successful_imported_files(data_date):
    return list(
        DataImportLog.objects.filter(
            data_date=data_date,
            status=DataImportLog.Status.SUCCESS,
        ).values_list('file_name', flat=True)
    )


# 列出成功导入的表
def list_successful_imported_tables(data_date):
    return sorted(
        {
            file_name.rsplit('_', 1)[0].upper() + '_HISTORY'
            for file_name in list_successful_imported_files(data_date)
            if file_name
        }
    )


# 列出结果导入依赖表
def list_result_import_dependencies():
    return [
        table_name.upper()
        for table_name in ResultImportDependency.objects
        .order_by('table_name')
        .values_list('table_name', flat=True)
        if table_name
    ]


# 获取未导入完成总行数据导入的依赖表
def get_missing_dependency_tables(data_date):
    required_tables = set(list_result_import_dependencies())
    if not required_tables:
        return []

    imported_tables = set(list_successful_imported_tables(data_date))
    return sorted(required_tables - imported_tables)


# 判断结果导入是否就绪
def is_result_import_ready(data_date):
    missing_tables = get_missing_dependency_tables(data_date)
    return len(missing_tables) == 0, missing_tables


# 获取结果导入日志
def get_result_import_log(data_date):
    return ResultImportLog.objects.filter(data_date=data_date).first()


# 标记结果导入状态
def mark_result_import_status(data_date, status, message=''):
    return ResultImportLog.objects.update_or_create(
        data_date=data_date,
        defaults={
            'status': status,
            'message': (message or '')[:1000],
        },
    )


def list_post_profit_indicator_logs(data_date):
    return ResultImportIndicatorLogPostProfit.objects.filter(data_date=data_date).order_by('indicator_id', 'id')


def list_successful_post_profit_indicator_ids(data_date):
    return list(
        ResultImportIndicatorLogPostProfit.objects.filter(
            data_date=data_date,
            status=ResultImportIndicatorLogPostProfit.Status.SUCCESS,
        ).values_list('indicator_id', flat=True)
    )


def has_running_post_profit_indicator_logs(data_date):
    return ResultImportIndicatorLogPostProfit.objects.filter(
        data_date=data_date,
        status=ResultImportIndicatorLogPostProfit.Status.RUNNING,
    ).exists()


def mark_post_profit_indicator_status(data_date, indicator_id, status, message='', rule_id=None):
    return ResultImportIndicatorLogPostProfit.objects.update_or_create(
        data_date=data_date,
        indicator_id=indicator_id,
        defaults={
            'rule_id': rule_id,
            'status': status,
            'message': (message or '')[:1000],
        },
    )
