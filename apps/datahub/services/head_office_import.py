import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Sequence
from django.conf import settings
from django.db import close_old_connections
from django.db.models import F
from apps.datahub.models import DataImportLog
import MySQLdb
import requests



LOGGER = logging.getLogger(__name__)

IMPORT_STATUS_PENDING = DataImportLog.Status.PENDING
IMPORT_STATUS_SUCCESS = DataImportLog.Status.SUCCESS
IMPORT_STATUS_FAILED = DataImportLog.Status.FAILED
IMPORT_STATUS_RUNNING = DataImportLog.Status.RUNNING

# 年末执行
YEAR_END_HISTORY_TABLES = {
    'I01_SZ_CONTEX_FINANCE_DATA_TBL',
}

# 数据清除需特殊处理+月末需要插入月表
SPECIAL_DELETE_HISTORY_TABLES = {
    'I01_SZ_BEHALF_PAY_DTL',
    'I01_SZ_CORP_CUST_BASIC_INFO',
    'I01_SZ_FIN_CORE_GL_SUBJ_BAL_INFO',
    'I01_SZ_INDIV_ASSET_DATA_TBL',
    'I01_SZ_INDIV_IMEDIATE_BIZ_DATA_TBL',
    'I01_SZ_INDIV_LABEL_DATA_TBL',
    'I01_SZ_INDIV_LOAN_BIZ_INFO',
}

# 表中对应的日期字段
TABLE_DATE_FIELDS = {
    'I01_SZ_FIN_CORE_GL_SUBJ_BAL_INFO': 'ACCNT_DT',
}


def get_required_env(name: str) -> str:
    value = (os.getenv(name) or '').strip()
    if not value:
        LOGGER.error(f'缺少环境变量: {name}')
        raise ValueError(f'缺少环境变量: {name}')
    return value


class HeadOfficeDataImporter:
    def __init__(self, date_str: str) -> None:
        self.date = date_str
        self.ymd_date = None
        self.base_dir = Path(get_required_env('AUTO_LOAD_DATA_BASE_DIR'))
        self.db_host = get_required_env('MYSQL_HOST')
        self.db_port = int(get_required_env('MYSQL_PORT'))
        self.db_user = get_required_env('MYSQL_USER')
        self.db_password = get_required_env('MYSQL_PASSWORD')
        self.db_name = get_required_env('MYSQL_DATABASE')
        self.host_data_base_dir = Path(get_required_env('HOST_DATA_BASE_DIR'))
        self.import_max_run_count = int(get_required_env('IMPORT_MAX_RUN_COUNT'))

        self._validate_inputs()

    # 验证输入参数
    def _validate_inputs(self) -> None:
        try:
            dt = datetime.strptime(self.date, '%Y-%m-%d')
        except Exception:
            LOGGER.error('date格式错误，应为%Y-%m-%d，当前值: %s', self.date)
            raise ValueError(f'date格式错误，应为%Y-%m-%d，当前值: {self.date}')

        self.ymd_date = dt.strftime('%Y%m%d')
        if not self.base_dir.exists():
            LOGGER.error('基础目录不存在: %s', self.base_dir)
            raise ValueError(f'基础目录不存在: {self.base_dir}')

    # 获取数据库连接
    def get_conn(self):
        return MySQLdb.connect(
            host=self.db_host,
            user=self.db_user,
            passwd=self.db_password,
            port=self.db_port,
            db=self.db_name,
            charset='utf8mb4',
        )

    # 从文件名中提取表名
    def extract_table_name_from_file(self, file_path: Path) -> str:
        base_name = file_path.stem
        if '_' not in base_name:
            LOGGER.error('文件名格式错误，无法提取表名: %s', file_path.name)
            raise ValueError(f'文件名格式错误，无法提取表名: {file_path.name}')
        return base_name.rsplit('_', 1)[0]


    # 清空每日表
    def delete_daily_table(self, cursor, table_name: str) -> None:
        cursor.execute(f'DELETE FROM `{table_name}`')

    # 获取非自增列
    def get_non_auto_increment_columns(self, cursor, table_name: str) -> List[str]:
        sql = """
        SELECT COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %s
          AND TABLE_NAME = %s
          AND NOT (COLUMN_KEY = 'PRI' AND EXTRA = 'auto_increment')
        ORDER BY ORDINAL_POSITION
        """
        cursor.execute(sql, (self.db_name, table_name))
        columns = [row[0] for row in cursor.fetchall()]
        if not columns:
            LOGGER.error('未找到表字段: %s', table_name)
            raise ValueError(f'未找到表字段: {table_name}')
        return columns

    # 将文件加载到每日表
    def load_file_to_daily_table(self, table_name: str, file_name: str, column_list: str) -> None:
        url = "http://host.docker.internal:5001/run-import"
        payload = {
            "file_path": str(self.host_data_base_dir / self.ymd_date / file_name),
            "table_name": f"{self.db_name}.{table_name}",
            "column_list": column_list,
        }

        try:
            resp = requests.post(url, json=payload, timeout=600)
        except Exception as e:
            LOGGER.exception(f'调用宿主机导入服务失败: {str(e)}')
            raise RuntimeError(f'调用宿主机导入服务失败: {str(e)}')

        if resp.status_code != 200:
            LOGGER.exception(f'导入服务HTTP异常 status={resp.status_code}, body={resp.text}')
            raise RuntimeError(f'导入服务HTTP异常 status={resp.status_code}, body={resp.text}')

        try:
            result = resp.json()
        except Exception:
            LOGGER.exception(f'导入服务返回非JSON: {resp.text}')
            raise RuntimeError(f'导入服务返回非JSON: {resp.text}')

        if result.get("code") != 0:
            LOGGER.exception(f'宿主机导入失败 table={table_name}, stderr={result.get("stderr")}')
            raise RuntimeError(
                f"宿主机导入失败 table={table_name}, stderr={result.get('stderr')}"
            )

    # 验证数据一致性
    def verify_data_consistency(self, cursor, table_name: str, file_path: Path) -> bool:
        cursor.execute(f'SELECT COUNT(*) FROM `{table_name}`')
        table_count = cursor.fetchone()[0]
        with file_path.open('r', encoding='utf-8', errors='ignore') as file_obj:
            file_count = sum(1 for _ in file_obj)
        LOGGER.info('数据核对 table=%s file_rows=%s table_rows=%s', table_name, file_count, table_count)
        return table_count == file_count

    # 刷新默认历史表
    def refresh_default_history(
        self, 
        cursor, 
        table_name: str, 
        column_list: str, 
        date_file_name='DATA_DT'
    ) -> None:
        cursor.execute(
            f'DELETE FROM `{table_name}_history` WHERE `{date_file_name}` = %s',
            (self.date,)
        )
        

        cursor.execute(
            f'INSERT INTO `{table_name}_history` ({column_list}) SELECT {column_list} FROM `{table_name}`'
        )

    # 刷新年末历史表
    def refresh_year_end_history(
        self, 
        cursor, 
        table_name: str, 
        column_list: str,
        date_file_name='DATA_DT'
    ) -> None:
        if self.date.endswith('12-31'):
            self.refresh_default_history(cursor, table_name, column_list, date_file_name)

    # 刷新特殊删除历史表
    def refresh_special_delete_history(
        self, 
        cursor, 
        table_name: str, 
        column_list: str,
        date_file_name='DATA_DT'
    ) -> None:
        cursor.execute(
            f'DELETE FROM `{table_name}_history` '
            f'WHERE `{date_file_name}` = %s OR `{date_file_name}` < DATE_SUB(%s, INTERVAL 1 MONTH)',
            (self.date, self.date),
        )
        cursor.execute(
            f'INSERT INTO `{table_name}_history` ({column_list}) SELECT {column_list} FROM `{table_name}`'
        )

        current_dt = datetime.strptime(self.date, '%Y-%m-%d')
        next_day = current_dt + timedelta(days=1)
        if next_day.month != current_dt.month:
            cursor.execute(
                f'DELETE FROM `{table_name}_month` WHERE `{date_file_name}` = %s',
                (self.date,)
            )
            cursor.execute(
                f'INSERT INTO `{table_name}_month` ({column_list}) SELECT {column_list} FROM `{table_name}`'
            )

    # 刷新历史表
    def refresh_history_table(self, cursor, table_name: str, column_list: str) -> None:
        date_file_name = TABLE_DATE_FIELDS.get(table_name, 'DATA_DT')
        if table_name in SPECIAL_DELETE_HISTORY_TABLES:
            self.refresh_special_delete_history(cursor, table_name, column_list, date_file_name)
            return

        if table_name in YEAR_END_HISTORY_TABLES:
            self.refresh_year_end_history(cursor, table_name, column_list, date_file_name)
            return

        self.refresh_default_history(cursor, table_name, column_list, date_file_name)

    # 更新或创建导入日志
    def upsert_import_log(self, file_name: str, status: int, message: str = 'success', **extra_defaults) -> None:
        close_old_connections()
        try:
            DataImportLog.objects.update_or_create(
                file_name=file_name,
                data_date=self.date,
                defaults={
                    'status': status,
                    'message': message[:1000],
                    **extra_defaults,
                },
            )
        finally:
            close_old_connections()

    def mark_file_running(self, file_name: str) -> None:
        close_old_connections()
        try:
            log, created = DataImportLog.objects.get_or_create(
                file_name=file_name,
                data_date=self.date,
                defaults={
                    'status': IMPORT_STATUS_RUNNING,
                    'message': 'running',
                    'run_count': 1,
                },
            )
            if created:
                return

            DataImportLog.objects.filter(pk=log.pk).update(
                status=IMPORT_STATUS_RUNNING,
                message='running',
                run_count=F('run_count') + 1,
            )
        finally:
            close_old_connections()


    # 执行导入任务
    def task(self, table_name: str, data_file: Path) -> str:
        conn = None
        cursor = None
        close_old_connections()
        try:
            conn = self.get_conn()
            cursor = conn.cursor()
            file_path = data_file.with_suffix('.txt')

            LOGGER.info('开始导入 table=%s file=%s data_date=%s', table_name, file_path, self.date)
            self.mark_file_running(data_file.name)
            self.delete_daily_table(cursor, table_name)
            columns = self.get_non_auto_increment_columns(cursor, table_name)
            column_list = ','.join(f'{column}' for column in columns)
            self.load_file_to_daily_table(table_name, file_path.name, column_list)

            if not self.verify_data_consistency(cursor, table_name, file_path):
                LOGGER.error('数据校验失败: %s', table_name)
                raise RuntimeError(f'数据校验失败: {table_name}')

            self.refresh_history_table(cursor, table_name, column_list)
            conn.commit()
            self.upsert_import_log(data_file.name, IMPORT_STATUS_SUCCESS)
            LOGGER.info('导入完成 table=%s file=%s', table_name, file_path.name)
            return data_file.name
        except Exception as exc:
            if conn:
                conn.rollback()
            self.upsert_import_log(data_file.name, IMPORT_STATUS_FAILED, str(exc))
            LOGGER.exception('导入失败 table=%s file=%s', table_name, data_file)
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
            close_old_connections()

    # 批量插入数据
    def insert_data(self, table_names: List[str], data_files: List[Path]):
        success_files: List[str] = []
        failed_files: List[str] = []

        for index, table_name in enumerate(table_names):
            try:
                file_name = data_files[index].name
                self.task(table_name, data_files[index])
                success_files.append(file_name)
            except Exception:
                failed_files.append(file_name)

        return {
            'success_files': sorted(success_files),
            'failed_files': sorted(failed_files),
        }

    # 过滤已处理的文件
    def filter_processed_files(self, files: Sequence[Path]) -> List[Path]:
        if not files:
            return []

        log_map = {
            row['file_name']: row
            for row in DataImportLog.objects.filter(data_date=self.date).values('file_name', 'status', 'run_count')
        }

        pending_files = []
        for file_path in files:
            log = log_map.get(file_path.name)
            if not log:
                pending_files.append(file_path)
                continue

            if log['status'] in [IMPORT_STATUS_SUCCESS, IMPORT_STATUS_PENDING, IMPORT_STATUS_RUNNING]:
                continue

            if (log.get('run_count') or 0) >= self.import_max_run_count:
                LOGGER.warning(
                    '文件重试次数已达上限，跳过导入 file=%s data_date=%s run_count=%s',
                    file_path.name,
                    self.date,
                    log.get('run_count'),
                )
                continue

            pending_files.append(file_path)

        return pending_files


    # 标记文件为待处理
    def mark_files_pending(self, files: Sequence[Path]) -> None:
        for file_path in files:
            self.upsert_import_log(file_path.name, IMPORT_STATUS_PENDING, 'pending')

    # 扫描文件
    def scan_files(self):
        dir_path = self.base_dir / self.ymd_date
        
        if not dir_path.exists():
            LOGGER.error('目录不存在: %s', dir_path)
            raise ValueError(f'目录不存在: {dir_path}')

        all_files = sorted(path for path in dir_path.glob('*.ok') if path.is_file())

        pending_files = self.filter_processed_files(all_files)
        self.mark_files_pending(pending_files)

        return {
            'all_files': all_files,
            'pending_files': pending_files,
        }

    # 运行导入
    def run(self):
        file_scan = self.scan_files()
        all_files = file_scan['all_files']
        pending_files = file_scan['pending_files']

        if not all_files:
            message = f'目录下未发现 .ok 文件 data_date={self.date}'
            LOGGER.info(message)
            return {
                'data_date': self.date,
                'status': 'no_files_found',
                'message': message,
                'total_files': 0,
                'pending_files': 0,
                'success_files': [],
                'failed_files': [],
            }

        if not pending_files:
            message = f'目录文件已全部导入 data_date={self.date}'
            LOGGER.info(message)
            return {
                'data_date': self.date,
                'status': 'already_processed',
                'message': message,
                'total_files': len(all_files),
                'pending_files': 0,
                'success_files': [],
                'failed_files': [],
            }

        table_names = [self.extract_table_name_from_file(file_path) for file_path in pending_files]
        result = self.insert_data(table_names, pending_files)
        status = 'success' if not result['failed_files'] else 'partial_failed'
        message = (
            f"导入完成 data_date={self.date} total={len(all_files)} "
            f"pending={len(pending_files)} success={len(result['success_files'])} "
            f"failed={len(result['failed_files'])}"
        )
        LOGGER.info(message)

        return {
            'data_date': self.date,
            'status': status,
            'message': message,
            'total_files': len(all_files),
            'pending_files': len(pending_files),
            'success_files': result['success_files'],
            'failed_files': result['failed_files'],
        }


def run_import(date_str: str):
    if not date_str:
        LOGGER.error('date_str is required')
        raise ValueError('date_str is required')
    
    if not settings.HEAD_OFFICE_IMPORT_BEAT_ENABLED:
        LOGGER.info('总行导入定时任务已禁用，跳过执行')
        return {
            'data_date': date_str,
            'status': 'disabled',
            'message': '总行导入定时任务已禁用',
            'total_files': 0,
            'pending_files': 0,
            'success_files': [],
            'failed_files': [],
        }
    
    importer = HeadOfficeDataImporter(date_str)
    LOGGER.info('开始执行总行数据导入 data_date=%s base_dir=%s', date_str, importer.base_dir)
    return importer.run()
