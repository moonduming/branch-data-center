from django.db import models

from common.models import ManualTableTimestampMixin


class PerfIndicator(ManualTableTimestampMixin):
    """业绩看板-指标定义表"""

    class Status(models.TextChoices):
        ENABLED = '01', '启用'
        DISABLED = '05', '停用'

    id = models.BigAutoField(primary_key=True, verbose_name='主键ID')
    indicator_code = models.CharField(max_length=64, unique=True, verbose_name='指标编码')
    indicator_name = models.CharField(max_length=128, verbose_name='指标名称')
    parent_id = models.BigIntegerField(null=True, blank=True, verbose_name='父指标ID')
    assessment_indicator_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        verbose_name='业绩考核指标ID',
    )
    category_code = models.CharField(max_length=32, null=True, blank=True, verbose_name='指标分类编码')
    category_name = models.CharField(max_length=64, null=True, blank=True, verbose_name='指标分类名称')
    line_code = models.CharField(max_length=64, null=True, blank=True, verbose_name='指标条线编码')
    indicator_standard = models.CharField(max_length=2, default='01', verbose_name='指标标准')
    display_unit = models.CharField(max_length=32, null=True, blank=True, verbose_name='显示单位')
    decimal_places = models.PositiveSmallIntegerField(default=2, verbose_name='小数位数')
    display_type = models.CharField(max_length=32, default='card', verbose_name='默认展示类型')
    display_scope = models.CharField(max_length=32, default='all', verbose_name='展示范围')
    show_in_card = models.BooleanField(default=False, verbose_name='是否展示在顶部卡片')
    show_in_trend = models.BooleanField(default=False, verbose_name='是否展示在趋势图下拉')
    show_in_rank = models.BooleanField(default=False, verbose_name='是否展示在排名下拉')
    sort_no = models.IntegerField(default=0, verbose_name='排序')
    status = models.CharField(
        max_length=2,
        choices=Status.choices,
        default=Status.ENABLED,
        verbose_name='状态',
    )
    description = models.CharField(max_length=1000, null=True, blank=True, verbose_name='指标描述')
    remark = models.CharField(max_length=1000, null=True, blank=True, verbose_name='备注')

    class Meta:
        db_table = 'perf_indicator'
        verbose_name = '业绩看板指标定义'
        managed = False
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['parent_id'], name='idx_parent_id'),
            models.Index(fields=['category_code'], name='idx_category_code'),
            models.Index(fields=['status', 'sort_no'], name='idx_status_sort'),
        ]


class PerfIndicatorRule(ManualTableTimestampMixin):
    """业绩看板-指标规则表"""

    class Status(models.TextChoices):
        ENABLED = '01', '启用'
        DISABLED = '05', '停用'

    id = models.BigAutoField(primary_key=True, verbose_name='主键ID')
    indicator_id = models.BigIntegerField(verbose_name='指标ID')
    rule_version = models.IntegerField(default=1, verbose_name='规则版本号')
    is_current = models.BooleanField(default=True, verbose_name='是否当前生效版本')
    rule_name = models.CharField(max_length=128, null=True, blank=True, verbose_name='规则名称')
    sql_template = models.TextField(verbose_name='指标计算SQL模板')
    target_sql_template = models.TextField(null=True, blank=True, verbose_name='目标值SQL模板')
    calc_mode = models.CharField(max_length=32, default='single_value', verbose_name='计算模式')
    result_fields = models.CharField(max_length=255, default='org_id,metric_value', verbose_name='SQL输出字段定义')
    org_prefix = models.CharField(max_length=64, null=True, blank=True, verbose_name='输出机构编码前缀')
    need_org_filter = models.BooleanField(default=True, verbose_name='是否需要按机构过滤')
    need_date_param = models.BooleanField(default=True, verbose_name='是否需要日期参数')
    need_day_count_param = models.BooleanField(default=False, verbose_name='是否需要天数参数')
    run_mode = models.CharField(max_length=32, default='all_org', verbose_name='执行模式')
    data_source_desc = models.CharField(max_length=255, null=True, blank=True, verbose_name='数据来源说明')
    display_value_field = models.CharField(max_length=64, default='metric_value', verbose_name='默认展示值字段')
    compare_value_field = models.CharField(max_length=64, null=True, blank=True, verbose_name='辅助比较字段')
    status = models.CharField(
        max_length=2,
        choices=Status.choices,
        default=Status.ENABLED,
        verbose_name='状态',
    )
    remark = models.CharField(max_length=1000, null=True, blank=True, verbose_name='备注')

    class Meta:
        db_table = 'perf_indicator_rule'
        verbose_name = '业绩看板指标规则'
        managed = False
        verbose_name_plural = verbose_name
        unique_together = (('indicator_id', 'rule_version'),)
        indexes = [
            models.Index(fields=['indicator_id', 'is_current'], name='idx_indicator_current'),
            models.Index(fields=['status'], name='idx_rule_status'),
        ]


class PerfIndicatorResult(ManualTableTimestampMixin):
    """业绩看板-指标结果表"""

    class CalcStatus(models.TextChoices):
        SUCCESS = '01', '成功'
        FAILED = '02', '失败'

    id = models.BigAutoField(primary_key=True, verbose_name='主键ID')
    data_dt = models.DateField(verbose_name='数据日期')
    indicator_id = models.BigIntegerField(verbose_name='指标ID')
    org_id = models.CharField(max_length=64, verbose_name='机构ID')
    metric_value = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, verbose_name='主指标值')
    metric_value_2 = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, verbose_name='辅助指标值2')
    metric_value_3 = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, verbose_name='辅助指标值3')
    target_value = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, verbose_name='目标值')
    completion_rate = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, verbose_name='完成率')
    rank_no = models.IntegerField(null=True, blank=True, verbose_name='排名')
    is_topn = models.BooleanField(default=False, verbose_name='是否进入排名展示')
    calc_status = models.CharField(
        max_length=2,
        choices=CalcStatus.choices,
        default=CalcStatus.SUCCESS,
        verbose_name='计算状态',
    )
    error_msg = models.CharField(max_length=1000, null=True, blank=True, verbose_name='计算失败原因')
    extra_json = models.JSONField(null=True, blank=True, verbose_name='扩展字段')

    class Meta:
        db_table = 'perf_indicator_result'
        verbose_name = '业绩看板指标结果'
        managed = False
        verbose_name_plural = verbose_name
        unique_together = (('data_dt', 'indicator_id', 'org_id'),)
        indexes = [
            models.Index(fields=['indicator_id', 'data_dt'], name='idx_indicator_dt'),
            models.Index(fields=['org_id', 'indicator_id', 'data_dt'], name='idx_org_indicator_dt'),
            models.Index(fields=['data_dt', 'indicator_id', 'rank_no'], name='idx_dt_rank'),
        ]


class DataImportLog(ManualTableTimestampMixin):
    """总行下发文件导入日志表。"""

    class Status(models.IntegerChoices):
        PENDING = 0, '待处理'
        SUCCESS = 1, '成功'
        FAILED = 2, '失败'
        RUNNING = 3, '执行中'

    id = models.BigAutoField(primary_key=True, verbose_name='主键ID')
    file_name = models.CharField(max_length=255, verbose_name='文件名')
    data_date = models.DateField(verbose_name='数据日期')
    run_count = models.PositiveIntegerField(default=0, verbose_name='运行次数')
    status = models.PositiveSmallIntegerField(
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='状态',
    )
    message = models.CharField(max_length=1000, null=True, blank=True, verbose_name='状态说明')

    class Meta:
        db_table = 'data_import_log'
        verbose_name = '总行文件导入日志'
        managed = False
        verbose_name_plural = verbose_name
        unique_together = (('file_name', 'data_date'),)
        indexes = [
            models.Index(fields=['data_date', 'file_name'], name='idx_import_dt_file'),
            models.Index(fields=['data_date', 'status'], name='idx_import_dt_status'),
        ]


class ResultImportDependency(ManualTableTimestampMixin):
    """结果表导入依赖表配置。"""

    id = models.BigAutoField(primary_key=True, verbose_name='主键ID')
    table_name = models.CharField(max_length=128, unique=True, verbose_name='依赖表名')
    remark = models.CharField(max_length=255, null=True, blank=True, verbose_name='备注')

    class Meta:
        db_table = 'result_import_dependency'
        verbose_name = '结果表导入依赖表'
        managed = False
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['table_name'], name='idx_result_dep_table'),
        ]


class ResultImportLog(ManualTableTimestampMixin):
    """结果表导入任务执行日志。"""

    class Status(models.IntegerChoices):
        PENDING = 0, '待处理'
        SUCCESS = 1, '成功'
        FAILED = 2, '失败'
        RUNNING = 3, '执行中'

    STATUS_PENDING = Status.PENDING
    STATUS_SUCCESS = Status.SUCCESS
    STATUS_FAILED = Status.FAILED
    STATUS_RUNNING = Status.RUNNING

    id = models.BigAutoField(primary_key=True, verbose_name='主键ID')
    data_date = models.DateField(unique=True, verbose_name='数据日期')
    status = models.PositiveSmallIntegerField(
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='状态',
    )
    message = models.CharField(max_length=1000, null=True, blank=True, verbose_name='状态说明')

    class Meta:
        db_table = 'result_import_log'
        verbose_name = '结果表导入日志'
        managed = False
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['data_date', 'status'], name='idx_result_import_dt_status'),
        ]


class PerfIndicatorRulePostProfit(ManualTableTimestampMixin):
    """分润指标规则表"""

    class Status(models.TextChoices):
        ENABLED = '01', '启用'
        DISABLED = '05', '停用'

    id = models.BigAutoField(primary_key=True, verbose_name='主键ID')
    indicator_id = models.BigIntegerField(verbose_name='指标ID')
    rule_version = models.IntegerField(default=1, verbose_name='规则版本号')
    is_current = models.BooleanField(default=True, verbose_name='是否当前生效版本')
    rule_name = models.CharField(max_length=128, null=True, blank=True, verbose_name='规则名称')
    point_sql_template = models.TextField(verbose_name='时点计算SQL模板')
    daily_avg_sql_template = models.TextField(verbose_name='日均计算SQL模板')
    calc_mode = models.CharField(max_length=32, default='single_value', verbose_name='计算模式')
    result_fields = models.CharField(
        max_length=255,
        default='org_id,employee_no,employee_name,metric_value,metric_value_2',
        verbose_name='SQL输出字段定义',
    )
    org_prefix = models.CharField(max_length=64, null=True, blank=True, verbose_name='输出机构编码前缀')
    need_org_filter = models.BooleanField(default=True, verbose_name='是否需要按机构过滤')
    need_date_param = models.BooleanField(default=True, verbose_name='是否需要日期参数')
    need_day_count_param = models.BooleanField(default=False, verbose_name='是否需要天数参数')
    run_mode = models.CharField(max_length=32, default='all_org', verbose_name='执行模式')
    data_source_desc = models.CharField(max_length=255, null=True, blank=True, verbose_name='数据来源说明')
    display_value_field = models.CharField(max_length=64, default='metric_value', verbose_name='默认展示值字段')
    compare_value_field = models.CharField(max_length=64, null=True, blank=True, verbose_name='辅助比较字段')
    status = models.CharField(
        max_length=2,
        choices=Status.choices,
        default=Status.ENABLED,
        verbose_name='状态',
    )
    remark = models.CharField(max_length=1000, null=True, blank=True, verbose_name='备注')

    class Meta:
        db_table = 'perf_indicator_rule_post_profit'
        verbose_name = '分润指标规则'
        managed = False
        verbose_name_plural = verbose_name
        unique_together = (('indicator_id', 'rule_version'),)
        indexes = [
            models.Index(fields=['indicator_id', 'is_current'], name='idx_pp_indicator_current'),
            models.Index(fields=['status'], name='idx_pp_rule_status'),
        ]


class PerfIndicatorResultPostProfit(ManualTableTimestampMixin):
    """分润后指标结果表"""

    class CalcStatus(models.TextChoices):
        SUCCESS = '01', '成功'
        FAILED = '02', '失败'

    id = models.BigAutoField(primary_key=True, verbose_name='主键ID')
    data_dt = models.DateField(verbose_name='数据日期')
    indicator_id = models.BigIntegerField(verbose_name='指标ID')
    org_id = models.CharField(max_length=64, verbose_name='机构ID')
    employee_no = models.CharField(max_length=32, verbose_name='认领员工编号')
    employee_name = models.CharField(max_length=50, null=True, blank=True, verbose_name='认领员工姓名')
    metric_value = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, verbose_name='主指标值')
    metric_value_2 = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, verbose_name='辅助指标值2')
    metric_value_3 = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, verbose_name='辅助指标值3')
    target_value = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, verbose_name='目标值')
    completion_rate = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, verbose_name='完成率')
    rank_no = models.IntegerField(null=True, blank=True, verbose_name='排名')
    is_topn = models.BooleanField(default=False, verbose_name='是否进入排名展示')
    calc_status = models.CharField(
        max_length=2,
        choices=CalcStatus.choices,
        default=CalcStatus.SUCCESS,
        verbose_name='计算状态',
    )
    error_msg = models.CharField(max_length=1000, null=True, blank=True, verbose_name='计算失败原因')
    extra_json = models.JSONField(null=True, blank=True, verbose_name='扩展字段')

    class Meta:
        db_table = 'perf_indicator_result_post_profit'
        verbose_name = '分润后指标结果'
        managed = False
        verbose_name_plural = verbose_name
        unique_together = (('data_dt', 'indicator_id', 'employee_no', 'org_id'),)
        indexes = [
            models.Index(fields=['indicator_id', 'data_dt'], name='idx_pp_indicator_dt'),
            models.Index(fields=['employee_no', 'indicator_id', 'data_dt'], name='idx_pp_emp_indicator_dt'),
            models.Index(fields=['org_id', 'employee_no', 'data_dt'], name='idx_pp_org_emp_dt'),
            models.Index(fields=['data_dt', 'indicator_id', 'rank_no'], name='idx_pp_dt_rank'),
        ]


class ResultImportIndicatorLogPostProfit(ManualTableTimestampMixin):
    """分润后结果表导入指标执行日志。"""

    class Status(models.IntegerChoices):
        PENDING = 0, '待处理'
        SUCCESS = 1, '成功'
        FAILED = 2, '失败'
        RUNNING = 3, '执行中'

    STATUS_PENDING = Status.PENDING
    STATUS_SUCCESS = Status.SUCCESS
    STATUS_FAILED = Status.FAILED
    STATUS_RUNNING = Status.RUNNING

    id = models.BigAutoField(primary_key=True, verbose_name='主键ID')
    data_date = models.DateField(verbose_name='任务日期')
    indicator_id = models.BigIntegerField(verbose_name='指标ID')
    rule_id = models.BigIntegerField(null=True, blank=True, verbose_name='规则ID')
    status = models.PositiveSmallIntegerField(
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='状态',
    )
    message = models.CharField(max_length=1000, null=True, blank=True, verbose_name='状态说明')

    class Meta:
        db_table = 'result_import_indicator_log_post_profit'
        verbose_name = '分润后结果表导入指标日志'
        managed = False
        verbose_name_plural = verbose_name
        unique_together = (('data_date', 'indicator_id'),)
        indexes = [
            models.Index(fields=['data_date', 'status'], name='idx_pp_ind_imp_dt_st'),
            models.Index(fields=['data_date', 'indicator_id'], name='idx_pp_ind_imp_dt_ind'),
        ]
