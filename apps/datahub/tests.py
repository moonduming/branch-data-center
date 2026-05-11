from datetime import date
from contextlib import nullcontext
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.datahub.models import ResultImportLog
from apps.datahub.services.post_profit_indicator_calculation import (
    execute_post_profit_rule_batch,
    persist_post_profit_rule_results,
)
from apps.datahub.services.data_backup import AutoLoadDataBackupService, resolve_backup_date
from apps.datahub.services.head_office_import import HeadOfficeDataImporter
from apps.datahub.services.import_pipeline import resolve_import_date
from apps.datahub.tasks import (
    run_auto_load_data_backup_task,
    run_datahub_post_profit_result_import,
    run_datahub_result_import,
    run_head_office_import,
)
from apps.datahub.views import (
    AutoLoadDataBackupTriggerView,
    HeadOfficeImportTriggerView,
    IndicatorOptionView,
    ResultImportPostProfitTriggerView,
    ResultImportTriggerView,
)


class ImportPipelineTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.admin_user = SimpleNamespace(is_authenticated=True, user_level='99')

    @override_settings(HEAD_OFFICE_IMPORT_DAY_OFFSET=2)
    @patch('apps.datahub.services.import_pipeline.timezone.localdate', return_value=date(2026, 3, 25))
    def test_resolve_import_date_uses_offset_when_missing(self, _mock_localdate):
        self.assertEqual(resolve_import_date(None), date(2026, 3, 23))

    @patch('apps.datahub.tasks.run_import')
    @patch('apps.datahub.tasks.resolve_import_date', return_value=date(2026, 3, 24))
    def test_run_head_office_import_returns_import_summary(
        self,
        _mock_resolve_import_date,
        mock_run_import,
    ):
        mock_run_import.return_value = {
            'status': 'success',
            'message': '导入完成',
            'failed_files': [],
            'success_files': ['A20260324.ok'],
        }

        result = run_head_office_import(data_dt='2026-03-24')

        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['summary']['success_files'], ['A20260324.ok'])

    @patch('apps.datahub.tasks.run_auto_load_data_backup')
    def test_run_auto_load_data_backup_task_returns_summary(self, mock_run_auto_load_data_backup):
        mock_run_auto_load_data_backup.return_value = {
            'status': 'success',
            'data_date': '2026-03-26',
            'archive_path': '/tmp/20260326.zip',
        }

        result = run_auto_load_data_backup_task(data_dt='2026-03-26')

        self.assertEqual(result['status'], 'success')
        mock_run_auto_load_data_backup.assert_called_once_with(data_dt='2026-03-26')

    @patch(
        'apps.datahub.tasks.get_result_import_log',
        return_value=SimpleNamespace(status=ResultImportLog.STATUS_SUCCESS),
    )
    @patch('apps.datahub.tasks.resolve_import_date', return_value=date(2026, 3, 24))
    def test_run_datahub_result_import_skips_when_already_successful(
        self,
        _mock_resolve_import_date,
        _mock_get_result_import_log,
    ):
        result = run_datahub_result_import(data_dt='2026-03-24')

        self.assertEqual(result['status'], 'skipped')

    @patch('apps.datahub.tasks.mark_result_import_status')
    @patch('apps.datahub.tasks.is_result_import_ready', return_value=(False, ['I01_SZ_ACCT_SUM_D']))
    @patch('apps.datahub.tasks.list_result_import_dependencies', return_value=['I01_SZ_ACCT_SUM_D'])
    @patch('apps.datahub.tasks.get_result_import_log', return_value=None)
    @patch('apps.datahub.tasks.resolve_import_date', return_value=date(2026, 3, 24))
    def test_run_datahub_result_import_waits_for_dependencies(
        self,
        _mock_resolve_import_date,
        _mock_get_result_import_log,
        _mock_list_result_import_dependencies,
        _mock_is_result_import_ready,
        mock_mark_result_import_status,
    ):
        result = run_datahub_result_import(data_dt='2026-03-24')

        self.assertEqual(result['status'], 'pending')
        self.assertEqual(result['missing_tables'], ['I01_SZ_ACCT_SUM_D'])
        mock_mark_result_import_status.assert_called_once()

    @patch('apps.datahub.views.run_head_office_import.delay', return_value=SimpleNamespace(id='task-1'))
    @patch('apps.datahub.views.resolve_import_date', return_value=date(2026, 3, 24))
    def test_head_office_trigger_view_submits_admin_task(self, mock_resolve_import_date, mock_delay):
        request = self.factory.post('/api/datahub/imports/head-office/trigger/', {}, format='json')
        force_authenticate(request, user=self.admin_user)

        response = HeadOfficeImportTriggerView.as_view()(request)

        self.assertEqual(response.status_code, 202)
        mock_resolve_import_date.assert_called_once_with(None)
        mock_delay.assert_called_once_with(data_dt='2026-03-24')

    @patch('apps.datahub.views.run_auto_load_data_backup_task.delay', return_value=SimpleNamespace(id='task-3'))
    @patch('apps.datahub.views.resolve_backup_date', return_value=date(2026, 3, 26))
    def test_backup_trigger_view_supports_manual_date(self, mock_resolve_backup_date, mock_delay):
        request = self.factory.post(
            '/api/datahub/imports/backup/trigger/',
            {'data_dt': '2026-03-20'},
            format='json',
        )
        force_authenticate(request, user=self.admin_user)

        response = AutoLoadDataBackupTriggerView.as_view()(request)

        self.assertEqual(response.status_code, 202)
        mock_resolve_backup_date.assert_called_once_with(date(2026, 3, 20))
        mock_delay.assert_called_once_with(data_dt='2026-03-26')

    @patch('apps.datahub.views.run_datahub_result_import.delay', return_value=SimpleNamespace(id='task-2'))
    @patch('apps.datahub.views.resolve_import_date', return_value=date(2026, 3, 24))
    def test_result_trigger_view_supports_manual_trigger(self, mock_resolve_import_date, mock_delay):
        request = self.factory.post(
            '/api/datahub/imports/result/trigger/',
            {'force': True},
            format='json',
        )
        force_authenticate(request, user=self.admin_user)

        response = ResultImportTriggerView.as_view()(request)

        self.assertEqual(response.status_code, 202)
        mock_resolve_import_date.assert_called_once_with(None)
        mock_delay.assert_called_once_with(data_dt='2026-03-24', force=True)

    @patch('apps.datahub.tasks.has_running_post_profit_indicator_logs', return_value=False)
    @patch('apps.datahub.tasks.list_successful_post_profit_indicator_ids', return_value=[101])
    @patch('apps.datahub.tasks.list_active_post_profit_rules', return_value=[{'id': 1, 'indicator_id': 101}])
    @patch('apps.datahub.tasks.resolve_import_date', return_value=date(2026, 3, 24))
    def test_run_datahub_post_profit_result_import_skips_when_already_successful(
        self,
        _mock_resolve_import_date,
        _mock_list_active_post_profit_rules,
        _mock_list_successful_post_profit_indicator_ids,
        _mock_has_running_post_profit_indicator_logs,
    ):
        result = run_datahub_post_profit_result_import(data_dt='2026-03-24')

        self.assertEqual(result['status'], 'skipped')

    @patch('apps.datahub.tasks.has_running_post_profit_indicator_logs', return_value=True)
    @patch('apps.datahub.tasks.list_active_post_profit_rules', return_value=[{'id': 1, 'indicator_id': 101}])
    @patch('apps.datahub.tasks.resolve_import_date', return_value=date(2026, 3, 24))
    def test_run_datahub_post_profit_result_import_skips_when_running(
        self,
        _mock_resolve_import_date,
        _mock_list_active_post_profit_rules,
        _mock_has_running_post_profit_indicator_logs,
    ):
        result = run_datahub_post_profit_result_import(data_dt='2026-03-24')

        self.assertEqual(result['status'], 'skipped')

    def test_run_datahub_post_profit_result_import_waits_for_dependencies(self):
        with patch('apps.datahub.tasks.resolve_import_date', return_value=date(2026, 3, 24)), patch(
            'apps.datahub.tasks.has_running_post_profit_indicator_logs',
            return_value=False,
        ), patch(
            'apps.datahub.tasks.list_active_post_profit_rules',
            return_value=[{'id': 1, 'indicator_id': 101}],
        ), patch(
            'apps.datahub.tasks.list_successful_post_profit_indicator_ids',
            return_value=[],
        ), patch(
            'apps.datahub.tasks.list_result_import_dependencies',
            return_value=['I01_SZ_ACCT_SUM_D'],
        ), patch(
            'apps.datahub.tasks.is_result_import_ready',
            return_value=(False, ['I01_SZ_ACCT_SUM_D']),
        ), patch('apps.datahub.tasks.execute_post_profit_indicator_rules') as mock_execute_post_profit_indicator_rules:
            result = run_datahub_post_profit_result_import(data_dt='2026-03-24')

        self.assertEqual(result['status'], 'pending')
        self.assertEqual(result['missing_tables'], ['I01_SZ_ACCT_SUM_D'])
        mock_execute_post_profit_indicator_rules.assert_not_called()

    @patch(
        'apps.datahub.tasks.execute_post_profit_indicator_rules',
        return_value={'rule_count': 1, 'success_count': 1, 'failed_count': 0, 'succeeded': [], 'failed': []},
    )
    @patch('apps.datahub.tasks.list_successful_post_profit_indicator_ids', side_effect=[[101], [101, 102]])
    @patch('apps.datahub.tasks.is_result_import_ready', return_value=(True, []))
    @patch('apps.datahub.tasks.list_result_import_dependencies', return_value=['I01_SZ_ACCT_SUM_D'])
    @patch(
        'apps.datahub.tasks.list_active_post_profit_rules',
        return_value=[{'id': 1, 'indicator_id': 101}, {'id': 2, 'indicator_id': 102}],
    )
    @patch('apps.datahub.tasks.has_running_post_profit_indicator_logs', return_value=False)
    @patch('apps.datahub.tasks.resolve_import_date', return_value=date(2026, 3, 24))
    def test_run_datahub_post_profit_result_import_only_runs_unsuccessful_indicators(
        self,
        _mock_resolve_import_date,
        _mock_has_running_post_profit_indicator_logs,
        _mock_list_active_post_profit_rules,
        _mock_list_result_import_dependencies,
        _mock_is_result_import_ready,
        _mock_list_successful_post_profit_indicator_ids,
        mock_execute_post_profit_indicator_rules,
    ):
        result = run_datahub_post_profit_result_import(data_dt='2026-03-24')

        self.assertEqual(result['status'], 'success')
        mock_execute_post_profit_indicator_rules.assert_called_once_with(
            import_date=date(2026, 3, 24),
            rules=[{'id': 2, 'indicator_id': 102}],
            org_id=None,
        )

    @patch(
        'apps.datahub.views.run_datahub_post_profit_result_import.delay',
        return_value=SimpleNamespace(id='task-4'),
    )
    @patch('apps.datahub.views.resolve_import_date', return_value=date(2026, 3, 24))
    def test_result_post_profit_trigger_view_supports_manual_trigger(self, mock_resolve_import_date, mock_delay):
        request = self.factory.post(
            '/api/datahub/imports/result/post-profit/trigger/',
            {'force': True},
            format='json',
        )
        force_authenticate(request, user=self.admin_user)

        response = ResultImportPostProfitTriggerView.as_view()(request)

        self.assertEqual(response.status_code, 202)
        mock_resolve_import_date.assert_called_once_with(None)
        mock_delay.assert_called_once_with(data_dt='2026-03-24', force=True)

    @patch('apps.datahub.views.PerfIndicator.objects.filter')
    def test_indicator_option_view_supports_indicator_name_search(self, mock_filter):
        queryset = MagicMock()
        queryset.order_by.return_value = queryset
        queryset.filter.return_value = queryset
        queryset.values.return_value = [{'id': 1, 'indicator_name': '存款余额'}]
        mock_filter.return_value = queryset

        request = self.factory.get('/api/datahub/indicator-options/', {'indicator_name': '存款'})
        force_authenticate(request, user=self.admin_user)

        response = IndicatorOptionView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        mock_filter.assert_called_once_with(status='01')
        queryset.filter.assert_called_once_with(indicator_name__icontains='存款')
        self.assertEqual(response.data['data'], [{'id': 1, 'indicator_name': '存款余额'}])

    @patch('apps.datahub.views.PerfIndicator.objects.filter')
    def test_indicator_option_view_returns_all_enabled_when_keyword_missing(self, mock_filter):
        queryset = MagicMock()
        queryset.order_by.return_value = queryset
        queryset.values.return_value = [{'id': 2, 'indicator_name': '贷款余额'}]
        mock_filter.return_value = queryset

        request = self.factory.get('/api/datahub/indicator-options/')
        force_authenticate(request, user=self.admin_user)

        response = IndicatorOptionView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        mock_filter.assert_called_once_with(status='01')
        self.assertEqual(response.data['data'], [{'id': 2, 'indicator_name': '贷款余额'}])


class AutoLoadDataBackupServiceTests(SimpleTestCase):
    @patch('apps.datahub.services.data_backup.timezone.localdate', return_value=date(2026, 4, 3))
    def test_resolve_backup_date_uses_yesterday_minus_seven_days(self, _mock_localdate):
        self.assertEqual(resolve_backup_date(None), date(2026, 3, 26))

    @patch.dict('os.environ', {'BACKUP_PASSWORD': 'secret'}, clear=False)
    def test_backup_service_rotates_existing_archive_before_creating_new_one(self):
        with TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            source_dir = base_dir / '20260326'
            archive_path = base_dir / '20260326.zip'
            source_dir.mkdir()
            archive_path.write_text('existing archive', encoding='utf-8')

            with patch.dict('os.environ', {'AUTO_LOAD_DATA_BASE_DIR': temp_dir}, clear=False):
                service = AutoLoadDataBackupService(data_dt='2026-03-26')

                def fake_subprocess_run(*args, **kwargs):
                    service.temp_archive_path.write_text('new archive', encoding='utf-8')
                    return SimpleNamespace(returncode=0, stdout='', stderr='')

                with patch('apps.datahub.services.data_backup.subprocess.run', side_effect=fake_subprocess_run):
                    result = service.run()

                rotated_archives = list(base_dir.glob('20260326.old.*.zip'))
                self.assertEqual(result['status'], 'success')
                self.assertFalse(source_dir.exists())
                self.assertEqual(len(rotated_archives), 1)
                self.assertEqual(rotated_archives[0].read_text(encoding='utf-8'), 'existing archive')
                self.assertEqual(archive_path.read_text(encoding='utf-8'), 'new archive')

    @patch.dict('os.environ', {'BACKUP_PASSWORD': 'secret'}, clear=False)
    @patch('apps.datahub.services.data_backup.shutil.which', return_value='/usr/bin/zip')
    def test_backup_service_removes_source_after_archive_created(self, _mock_which):
        with TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            source_dir = base_dir / '20260326'
            source_dir.mkdir()
            (source_dir / 'data.txt').write_text('payload', encoding='utf-8')

            with patch.dict('os.environ', {'AUTO_LOAD_DATA_BASE_DIR': temp_dir}, clear=False):
                service = AutoLoadDataBackupService(data_dt='2026-03-26')

                def fake_subprocess_run(*args, **kwargs):
                    service.temp_archive_path.write_text('archive bytes', encoding='utf-8')
                    return SimpleNamespace(returncode=0, stdout='', stderr='')

                with patch('apps.datahub.services.data_backup.subprocess.run', side_effect=fake_subprocess_run):
                    result = service.run()

                self.assertEqual(result['status'], 'success')
                self.assertFalse(source_dir.exists())
                self.assertTrue(service.archive_path.exists())


class HeadOfficeImportServiceTests(SimpleTestCase):
    def build_importer(self):
        importer = HeadOfficeDataImporter.__new__(HeadOfficeDataImporter)
        importer.date = '2026-03-24'
        importer.import_max_run_count = 3
        return importer

    @patch('apps.datahub.services.head_office_import.close_old_connections')
    @patch('apps.datahub.services.head_office_import.DataImportLog.objects.filter')
    @patch('apps.datahub.services.head_office_import.DataImportLog.objects.get_or_create')
    def test_mark_file_running_increments_run_count_for_existing_log(
        self,
        mock_get_or_create,
        mock_filter,
        _mock_close_old_connections,
    ):
        importer = self.build_importer()
        mock_get_or_create.return_value = (SimpleNamespace(pk=1), False)

        importer.mark_file_running('A.ok')

        mock_filter.assert_called_once_with(pk=1)
        mock_filter.return_value.update.assert_called_once()
        update_kwargs = mock_filter.return_value.update.call_args.kwargs
        self.assertEqual(update_kwargs['status'], 3)
        self.assertEqual(update_kwargs['message'], 'running')

    @patch('apps.datahub.services.head_office_import.DataImportLog.objects.filter')
    def test_filter_processed_files_skips_files_reaching_max_run_count(self, mock_filter):
        importer = self.build_importer()
        file_a = Path('/tmp/A.ok')
        file_b = Path('/tmp/B.ok')
        file_c = Path('/tmp/C.ok')

        values_qs = MagicMock()
        values_qs.values.return_value = [
            {'file_name': 'A.ok', 'status': 2, 'run_count': 3},
            {'file_name': 'B.ok', 'status': 2, 'run_count': 2},
            {'file_name': 'C.ok', 'status': 1, 'run_count': 1},
        ]
        mock_filter.return_value = values_qs

        result = importer.filter_processed_files([file_a, file_b, file_c])

        self.assertEqual(result, [file_b])


class PostProfitIndicatorCalculationTests(SimpleTestCase):
    def test_execute_post_profit_rule_batch_stops_after_first_failed_day(self):
        rule = SimpleNamespace(id=1, indicator_id=101)
        successful_day = {'written_count': 1}

        with patch(
            'apps.datahub.services.post_profit_indicator_calculation.get_post_profit_rule',
            return_value=rule,
        ), patch(
            'apps.datahub.services.post_profit_indicator_calculation.execute_post_profit_rule_for_date',
            side_effect=[successful_day, RuntimeError('boom')],
        ) as mock_execute_day, patch(
            'apps.datahub.services.post_profit_indicator_calculation.transaction.atomic',
            return_value=nullcontext(),
        ):
            with self.assertRaises(RuntimeError):
                execute_post_profit_rule_batch(rule_id=1, data_dt='2026-03-24', window_days=3)

        self.assertEqual(mock_execute_day.call_count, 2)

    @patch('apps.datahub.services.post_profit_indicator_calculation.PerfIndicatorResultPostProfit.objects.update_or_create')
    def test_persist_post_profit_rule_results_uses_employee_dimension(self, mock_update_or_create):
        rule = SimpleNamespace(id=1, indicator_id=101)

        written_count = persist_post_profit_rule_results(
            rule=rule,
            params={'data_dt': '2026-03-24'},
            daily_avg_rows=[
                {'org_id': '44030101', 'employee_no': 'E001', 'employee_name': '张三', 'metric_value': 12},
            ],
            point_rows=[
                {'org_id': '44030101', 'employee_no': 'E001', 'employee_name': '张三', 'metric_value_2': 34},
            ],
        )

        self.assertEqual(written_count, 1)
        mock_update_or_create.assert_called_once()
        call_kwargs = mock_update_or_create.call_args.kwargs
        self.assertEqual(call_kwargs['org_id'], '44030101')
        self.assertEqual(call_kwargs['employee_no'], 'E001')
        self.assertEqual(call_kwargs['defaults']['employee_name'], '张三')
