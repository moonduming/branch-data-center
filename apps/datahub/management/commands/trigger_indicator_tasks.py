from django.core.management.base import BaseCommand

from apps.datahub.tasks import execute_indicator_rule, schedule_all_indicator_rules


class Command(BaseCommand):
    help = '触发指标计算任务，可执行全部规则或单条规则。'

    def add_arguments(self, parser):
        parser.add_argument('--rule-id', type=int, help='指定规则ID，仅执行单条规则')
        parser.add_argument('--data-dt', type=str, help='数据日期，格式 YYYY-MM-DD')
        parser.add_argument('--day-count', type=int, help='天数参数')
        parser.add_argument('--org-id', type=str, help='机构ID参数')

    def handle(self, *args, **options):
        payload = {
            'data_dt': options.get('data_dt'),
            'day_count': options.get('day_count'),
            'org_id': options.get('org_id'),
        }

        rule_id = options.get('rule_id')
        if rule_id:
            async_result = execute_indicator_rule.delay(rule_id=rule_id, **payload)
            self.stdout.write(self.style.SUCCESS(f'已提交单条规则任务，rule_id={rule_id}, task_id={async_result.id}'))
            return

        async_result = schedule_all_indicator_rules.delay(**payload)
        self.stdout.write(self.style.SUCCESS(f'已提交全部规则调度任务，task_id={async_result.id}'))
