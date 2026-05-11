from django.db import models
from common.models import ManualTableTimestampMixin


class ProcessDefStatus(models.TextChoices):
    DRAFT = 'draft', '草稿'
    ACTIVE = 'active', '启用'
    INACTIVE = 'inactive', '停用'


class ProcessBusinessType(models.TextChoices):
    REPORT_SUBMIT = 'report_submit', '报表'
    PERFORMANCE_CLAIM = 'performance_claim', '业绩认领'
    PERFORMANCE_TRANSFER = 'performance_transfer', '业绩移交'


class InstanceStatus(models.TextChoices):
    RUNNING = 'running', '进行中'
    FINISHED = 'finished', '已完成'
    REJECTED = 'rejected', '已驳回'
    CANCELLED = 'cancelled', '已取消'


class TaskStatus(models.TextChoices):
    PENDING = 'pending', '待处理'
    PROCESSING = 'processing', '处理中'
    APPROVED = 'approved', '已通过'
    REJECTED = 'rejected', '已驳回'
    RETURNED = 'returned', '已退回'
    CANCELLED = 'cancelled', '已取消'
    SKIPPED = 'skipped', '已跳过'


class TaskResult(models.TextChoices):
    AGREE = 'agree', '同意'
    REJECT = 'reject', '驳回'
    RETURN = 'return', '退回'
    AUTO_PASS = 'auto_pass', '自动通过'
    AUTO_SKIP = 'auto_skip', '自动跳过'


class TransitionActionCode(models.TextChoices):
    SUBMIT = 'submit', '提交'
    APPROVE = 'approve', '审批通过'
    REJECT = 'reject', '驳回'
    RETURN = 'return', '退回'
    AUTO = 'auto', '自动流转'
    COMPLETE = 'complete', '完成'
    CANCEL = 'cancel', '取消'


class TaskLogAction(models.TextChoices):
    START = 'start', '发起流程'
    CREATE_TASK = 'create_task', '创建任务'
    CLAIM = 'claim', '签收任务'
    APPROVE = 'approve', '审批通过'
    REJECT = 'reject', '驳回'
    RETURN = 'return', '退回'
    RECALL = 'recall', '撤回'
    AUTO_FLOW = 'auto_flow', '自动流转'
    AUTO_SKIP = 'auto_skip', '自动跳过'
    CANCEL_TASK = 'cancel_task', '取消任务'
    JOIN_PASS = 'join_pass', '汇聚通过'
    FINISH = 'finish', '流程结束'
    CANCEL = 'cancel', '流程取消'


class AssigneeRuleType(models.TextChoices):
    APPLICANT = 'applicant', '发起人本人'
    EMPLOYEE_LEVEL = 'employee_level', '按员工级别'
    FIXED_USER = 'fixed_user', '固定用户'


class NodeType(models.TextChoices):
    START = 'start', '开始节点'
    MANUAL = 'manual', '人工审核节点'
    AUTO = 'auto', '自动处理节点'
    END = 'end', '结束节点'


class JoinStrategy(models.TextChoices):
    ALL_PASS = 'all_pass', '全部通过'
    ANY_PASS = 'any_pass', '任意通过'


class ConditionType(models.TextChoices):
    NONE = 'none', '无条件'
    SCRIPT = 'script', '脚本'


# 流程定义表
class WfProcessDef(ManualTableTimestampMixin):
    id = models.BigAutoField(primary_key=True, verbose_name='主键ID')
    process_code = models.CharField(max_length=50, verbose_name='流程编码')
    process_name = models.CharField(max_length=100, verbose_name='流程名称')
    business_type = models.CharField(
        max_length=50,
        choices=ProcessBusinessType.choices,
        verbose_name='业务类型'
    )
    version = models.IntegerField(verbose_name='版本号')
    status = models.CharField(
        max_length=20,
        choices=ProcessDefStatus.choices,
        default=ProcessDefStatus.DRAFT,
        verbose_name='状态'
    )
    is_latest = models.BooleanField(default=True, verbose_name='是否最新版本')
    remark = models.CharField(max_length=500, null=True, blank=True, verbose_name='备注')

    class Meta:
        unique_together = (('process_code', 'version'),)
        indexes = [
            models.Index(fields=['business_type'], name='idx_wf_proc_business'),
            models.Index(fields=['status'], name='idx_wf_proc_status'),
            models.Index(fields=['is_latest'], name='idx_wf_proc_is_latest'),
        ]
        managed = False
        db_table = 'wf_process_def'


# 节点定义表
class WfNodeDef(ManualTableTimestampMixin):
    id = models.BigAutoField(primary_key=True, verbose_name='主键ID')
    process_def_id = models.BigIntegerField(verbose_name='流程定义ID')
    node_code = models.CharField(max_length=50, verbose_name='节点编码')
    node_name = models.CharField(max_length=100, verbose_name='节点名称')
    node_type = models.CharField(
        max_length=30,
        choices=NodeType.choices,
        verbose_name='节点类型'
    )
    auto_func_name = models.CharField(max_length=100, null=True, blank=True, verbose_name='自动节点执行函数名')
    node_order = models.IntegerField(null=True, blank=True, verbose_name='节点顺序')
    is_parallel = models.BooleanField(default=False, verbose_name='是否并行节点')
    parallel_mode = models.CharField(max_length=30, null=True, blank=True, verbose_name='并行模式')
    join_strategy = models.CharField(
        max_length=30,
        choices=JoinStrategy.choices,
        null=True,
        blank=True,
        verbose_name='汇聚策略'
    )
    can_reject = models.BooleanField(default=False, verbose_name='是否允许驳回')
    can_return = models.BooleanField(default=False, verbose_name='是否允许退回')
    auto_create_task = models.BooleanField(default=True, verbose_name='是否自动创建任务')
    remark = models.CharField(max_length=500, null=True, blank=True, verbose_name='备注')

    class Meta:
        unique_together = (('process_def_id', 'node_code'),)
        indexes = [
            models.Index(fields=['node_code'], name='idx_wf_node_code'),
        ]
        managed = False
        db_table = 'wf_node_def'


# 节点审批人规则表
class WfNodeAssigneeRule(ManualTableTimestampMixin):
    id = models.BigAutoField(primary_key=True, verbose_name='主键ID')
    process_def_id = models.BigIntegerField(verbose_name='流程定义ID')
    node_code = models.CharField(max_length=50, verbose_name='节点编码')
    rule_type = models.CharField(
        max_length=30,
        choices=AssigneeRuleType.choices,
        verbose_name='规则类型'
    )
    rule_value = models.CharField(max_length=200, null=True, blank=True, verbose_name='规则值')
    remark = models.CharField(max_length=500, null=True, blank=True, verbose_name='备注')

    class Meta:
        unique_together = (('process_def_id', 'node_code'),)
        indexes = [
            models.Index(fields=['rule_type'], name='idx_wf_rule_type'),
        ]
        managed = False
        db_table = 'wf_node_assignee_rule'


# 流转定义表
class WfTransitionDef(ManualTableTimestampMixin):
    id = models.BigAutoField(primary_key=True, verbose_name='主键ID')
    process_def_id = models.BigIntegerField(verbose_name='流程定义ID')
    from_node_code = models.CharField(max_length=50, verbose_name='来源节点编码')
    to_node_code = models.CharField(max_length=50, verbose_name='目标节点编码')
    action_code = models.CharField(
        max_length=30,
        choices=TransitionActionCode.choices,
        verbose_name='动作编码'
    )
    condition_type = models.CharField(
        max_length=30,
        choices=ConditionType.choices,
        null=True,
        blank=True,
        verbose_name='条件类型'
    )
    condition_expr = models.CharField(max_length=1000, null=True, blank=True, verbose_name='条件表达式')
    priority = models.IntegerField(default=100, verbose_name='优先级（数值越小优先级越高）')
    is_enabled = models.BooleanField(default=True, verbose_name='是否启用')
    remark = models.CharField(max_length=500, null=True, blank=True, verbose_name='备注')

    class Meta:
        unique_together = (('process_def_id', 'from_node_code', 'to_node_code', 'action_code'),)
        indexes = [
            models.Index(fields=['from_node_code'], name='idx_wf_trans_from_node'),
            models.Index(fields=['to_node_code'], name='idx_wf_trans_to_node'),
        ]
        managed = False
        db_table = 'wf_transition_def'


# 流程实例表
class WfInstance(ManualTableTimestampMixin):
    id = models.BigAutoField(primary_key=True, verbose_name='主键ID')
    title = models.CharField(max_length=200, null=True, blank=True, verbose_name='实例标题')
    process_def_id = models.BigIntegerField(verbose_name='流程定义ID')
    business_type = models.CharField(max_length=50, verbose_name='业务类型')
    business_id = models.BigIntegerField(null=True, blank=True, verbose_name='业务ID')
    applicant_id = models.BigIntegerField(verbose_name='发起人ID')
    applicant_name = models.CharField(max_length=100, null=True, blank=True, verbose_name='发起人姓名')
    current_node_code = models.CharField(max_length=50, null=True, blank=True, verbose_name='当前节点编码')
    current_node_name = models.CharField(max_length=100, null=True, blank=True, verbose_name='当前节点名称')
    status = models.CharField(
        max_length=20,
        choices=InstanceStatus.choices,
        default=InstanceStatus.RUNNING,
        verbose_name='实例状态'
    )
    start_time = models.DateTimeField(verbose_name='开始时间')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')

    class Meta:
        indexes = [
            models.Index(fields=['process_def_id'], name='idx_wf_inst_proc_def'),
            models.Index(fields=['business_type', 'business_id'], name='idx_wf_inst_business'),
            models.Index(fields=['applicant_id'], name='idx_wf_inst_applicant'),
            models.Index(fields=['status'], name='idx_wf_inst_status'),
            models.Index(fields=['current_node_code'], name='idx_wf_inst_curr_node'),
        ]
        managed = False
        db_table = 'wf_instance'


# 流程任务表
class WfTask(ManualTableTimestampMixin):
    id = models.BigAutoField(primary_key=True, verbose_name='主键ID')
    instance_id = models.BigIntegerField(verbose_name='流程实例ID')
    node_code = models.CharField(max_length=50, verbose_name='节点编码')
    node_name = models.CharField(max_length=100, verbose_name='节点名称')
    assignee_id = models.BigIntegerField(null=True, blank=True, verbose_name='实际处理人ID')
    assignee_name = models.CharField(max_length=100, null=True, blank=True, verbose_name='实际处理人姓名')
    branch_key = models.CharField(max_length=100, null=True, blank=True, verbose_name='分支标识')
    parallel_group = models.CharField(max_length=100, null=True, blank=True, verbose_name='并行组标识')
    status = models.CharField(
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.PENDING,
        verbose_name='任务状态'
    )
    result = models.CharField(
        max_length=20,
        choices=TaskResult.choices,
        null=True,
        blank=True,
        verbose_name='处理结果'
    )
    round_no = models.IntegerField(default=1, verbose_name='审批轮次')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='节点完成时间')

    class Meta:
        indexes = [
            models.Index(fields=['assignee_id'], name='idx_wf_task_assignee'),
            models.Index(fields=['status'], name='idx_wf_task_status'),
            models.Index(fields=['parallel_group'], name='idx_wf_task_parallel'),
            models.Index(fields=['node_code'], name='idx_wf_task_node_code'),
            models.Index(fields=['instance_id', 'status'], name='idx_wf_task_inst_status'),
        ]
        managed = False
        db_table = 'wf_task'


# 审批分配表
class WfApprovalAssignment(ManualTableTimestampMixin):
    id = models.BigAutoField(primary_key=True, verbose_name='主键ID')
    instance_id = models.BigIntegerField(verbose_name='流程实例ID')
    task_id = models.BigIntegerField(null=True, blank=True, verbose_name='流程任务ID')
    node_code = models.CharField(max_length=50, verbose_name='节点编码')
    node_name = models.CharField(max_length=100, verbose_name='节点名称')
    assignee_id = models.BigIntegerField(verbose_name='审批人ID')
    assignee_name = models.CharField(max_length=100, null=True, blank=True, verbose_name='审批人姓名')
    round_no = models.IntegerField(default=1, verbose_name='审批轮次')
    result = models.CharField(
        max_length=20,
        choices=TaskResult.choices,
        null=True,
        blank=True,
        verbose_name='处理结果'
    )
    received_at = models.DateTimeField(null=True, blank=True, verbose_name='进入待办时间')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='查看时间')
    handled_at = models.DateTimeField(null=True, blank=True, verbose_name='处理时间')
    comment = models.CharField(max_length=1000, null=True, blank=True, verbose_name='处理意见')

    class Meta:
        indexes = [
            models.Index(fields=['instance_id'], name='idx_wf_assign_inst'),
            models.Index(fields=['task_id'], name='idx_wf_assign_task'),
            models.Index(fields=['assignee_id'], name='idx_wf_assign_user'),
            models.Index(fields=['instance_id', 'node_code'], name='idx_wf_assign_inst_node'),
        ]
        managed = False
        db_table = 'wf_approval_assignment'


# 流程日志表
class WfTaskLog(ManualTableTimestampMixin):
    id = models.BigAutoField(primary_key=True, verbose_name='主键ID')
    instance_id = models.BigIntegerField(verbose_name='流程实例ID')
    task_id = models.BigIntegerField(null=True, blank=True, verbose_name='任务ID')
    branch_key = models.CharField(max_length=100, null=True, blank=True, verbose_name='分支标识')
    parallel_group = models.CharField(max_length=100, null=True, blank=True, verbose_name='并行组标识')
    action = models.CharField(
        max_length=50,
        choices=TaskLogAction.choices,
        verbose_name='动作类型'
    )
    from_node_code = models.CharField(max_length=50, null=True, blank=True, verbose_name='来源节点编码')
    from_node_name = models.CharField(max_length=100, null=True, blank=True, verbose_name='来源节点名称')
    to_node_code = models.CharField(max_length=50, null=True, blank=True, verbose_name='目标节点编码')
    to_node_name = models.CharField(max_length=100, null=True, blank=True, verbose_name='目标节点名称')
    operator_id = models.BigIntegerField(null=True, blank=True, verbose_name='操作人ID')
    operator_name = models.CharField(max_length=100, null=True, blank=True, verbose_name='操作人姓名')
    result = models.CharField(
        max_length=20,
        choices=TaskResult.choices,
        null=True,
        blank=True,
        verbose_name='处理结果'
    )
    comment = models.CharField(max_length=1000, null=True, blank=True, verbose_name='备注说明')

    class Meta:
        indexes = [
            models.Index(fields=['instance_id'], name='idx_wf_log_instance'),
            models.Index(fields=['task_id'], name='idx_wf_log_task'),
            models.Index(fields=['action'], name='idx_wf_log_action'),
            models.Index(fields=['created_at'], name='idx_wf_log_created'),
            models.Index(fields=['branch_key'], name='idx_wf_log_branch'),
            models.Index(fields=['parallel_group'], name='idx_wf_log_parallel'),
        ]
        managed = False
        db_table = 'wf_task_log'
