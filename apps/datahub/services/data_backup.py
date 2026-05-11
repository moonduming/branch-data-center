import logging
import os
import shutil
import subprocess
from datetime import date, datetime, timedelta
from pathlib import Path

from django.utils import timezone


LOGGER = logging.getLogger(__name__)

BACKUP_TARGET_DAY_OFFSET = int(os.getenv('BACKUP_TARGET_DAY_OFFSET', '7'))

def get_required_env(name: str) -> str:
    value = (os.getenv(name) or '').strip()
    if not value:
        LOGGER.error('缺少环境变量: %s', name)
        raise ValueError(f'缺少环境变量: {name}')
    return value


def resolve_backup_date(data_dt=None) -> date:
    if data_dt is None:
        yesterday = timezone.localdate() - timedelta(days=1)
        return yesterday - timedelta(days=BACKUP_TARGET_DAY_OFFSET)

    if isinstance(data_dt, date):
        return data_dt

    if isinstance(data_dt, str):
        try:
            return datetime.strptime(data_dt, '%Y-%m-%d').date()
        except ValueError as exc:
            raise ValueError(f'data_dt格式错误，应为%Y-%m-%d，当前值: {data_dt}') from exc

    raise ValueError(f'不支持的data_dt类型: {type(data_dt)!r}')


class AutoLoadDataBackupService:
    def __init__(self, data_dt=None):
        self.data_date = resolve_backup_date(data_dt)
        self.base_dir = Path(get_required_env('AUTO_LOAD_DATA_BASE_DIR'))
        self.password = get_required_env('BACKUP_PASSWORD')
        self.folder_name = self.data_date.strftime('%Y%m%d')
        self.source_dir = self.base_dir / self.folder_name
        self.archive_path = self.base_dir / f'{self.folder_name}.zip'
        self.temp_archive_path = self.base_dir / f'.{self.folder_name}.zip.tmp'

        self._validate_base_dir()

    def run(self):
        if not self.source_dir.exists() or not self.source_dir.is_dir():
            message = f'待备份目录不存在，跳过备份 data_dt={self.data_date.isoformat()}'
            LOGGER.info(message)
            return self._build_result('skipped', message)

        renamed_archive_path = self._rotate_existing_archive()

        self._create_archive()
        shutil.rmtree(self.source_dir)
        if renamed_archive_path:
            message = (
                f'数据备份完成并已删除原目录 data_dt={self.data_date.isoformat()}，'
                f'旧备份已重命名为 {renamed_archive_path.name}'
            )
        else:
            message = f'数据备份完成并已删除原目录 data_dt={self.data_date.isoformat()}'
        LOGGER.info(message)
        return self._build_result('success', message)


    def _rotate_existing_archive(self):
        if not self.archive_path.exists():
            return None

        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        candidate = self.base_dir / f'{self.folder_name}.old.{timestamp}.zip'
        index = 1
        while candidate.exists():
            candidate = self.base_dir / f'{self.folder_name}.old.{timestamp}.{index}.zip'
            index += 1

        self.archive_path.rename(candidate)
        LOGGER.info('检测到旧备份文件，已重命名 archive=%s -> %s', self.archive_path, candidate)
        return candidate


    def _validate_base_dir(self):
        if not self.base_dir.exists() or not self.base_dir.is_dir():
            LOGGER.error('基础目录不存在: %s', self.base_dir)
            raise ValueError(f'基础目录不存在: {self.base_dir}')

    def _create_archive(self):
        zip_binary = shutil.which('zip')
        if not zip_binary:
            raise RuntimeError('系统未安装 zip 命令，无法创建加密压缩包')

        if self.temp_archive_path.exists():
            self.temp_archive_path.unlink()

        command = [
            zip_binary,
            '-r',
            '-q',
            '-P',
            self.password,
            str(self.temp_archive_path),
            self.folder_name,
        ]
        try:
            subprocess.run(
                command,
                cwd=self.base_dir,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            if self.temp_archive_path.exists():
                self.temp_archive_path.unlink()
            error_message = (exc.stderr or exc.stdout or str(exc)).strip()
            LOGGER.exception('创建备份压缩包失败 data_dt=%s', self.data_date)
            raise RuntimeError(f'创建备份压缩包失败: {error_message}') from exc

        if not self.temp_archive_path.exists():
            raise RuntimeError(f'备份压缩包创建失败，未生成文件: {self.temp_archive_path}')

        self.temp_archive_path.replace(self.archive_path)

    def _build_result(self, status, message):
        return {
            'status': status,
            'data_date': self.data_date.isoformat(),
            'folder_name': self.folder_name,
            'archive_path': str(self.archive_path),
            'source_dir': str(self.source_dir),
            'message': message,
        }


def run_auto_load_data_backup(data_dt=None):
    return AutoLoadDataBackupService(data_dt=data_dt).run()
