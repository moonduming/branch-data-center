from django.db import models

from common.models import ManualTableTimestampMixin

# 机构表
class OrgUnit(ManualTableTimestampMixin):
    class Status(models.TextChoices):
        NORMAL = "01", "正常"
        DISABLED = "05", "停用"
        CANCELLED = "09", "取消"

    class OrgType(models.TextChoices):
        BRANCH = "00", "分行"
        DEPT = "01", "部门"
        SUB_BRANCH = "02", "支行"
        TEAM = "03", "直营"

    id = models.BigAutoField(primary_key=True)
    org_code = models.CharField("机构编码", max_length=32, unique=True)
    credit_org_code = models.CharField("贷系统机构编码", max_length=32, null=True, blank=True)
    virtual_employee_no = models.CharField("公共虚拟员工号", max_length=32, null=True, blank=True)
    org_name = models.CharField("机构名称", max_length=100)
    org_type = models.CharField(
        "机构类型",
        max_length=2,
        choices=OrgType.choices,
    )
    is_assessment_dept = models.BooleanField("是否考核部门", default=False)
    leader_employee_no = models.CharField("主管领导员工号", max_length=32, null=True, blank=True)
    manager_employee_no = models.CharField("单位负责人员工号", max_length=32, null=True, blank=True)
    display_order = models.IntegerField("排序号", default=0)
    status = models.CharField(
        "状态",
        max_length=2,
        choices=Status.choices,
        default=Status.NORMAL,
    )
    parent_id = models.BigIntegerField("父机构ID", null=True, blank=True)
    remark = models.CharField("备注", max_length=255, null=True, blank=True)
    class Meta:
        db_table = "shenzhen_org_unit"
        managed = False
        verbose_name = "机构"
        verbose_name_plural = "机构"


# 用户机构关系表
class UserOrgRelation(ManualTableTimestampMixin):
    class Status(models.TextChoices):
        NORMAL = "01", "正常"
        INVALID = "09", "失效"

    class EmployeeLevel(models.TextChoices):
        BRANCH_LEADER = "00", "分行领导"
        DEPT_LEADER = "10", "部室领导"
        DEPT_SUPERVISOR = "13", "部室主管"
        DEPT_STAFF = "15", "部室员工"
        SUB_BRANCH_LEADER = "20", "支行领导"
        SUB_BRANCH_SUPERVISOR = "23", "支行主管"
        SUB_BRANCH_STAFF = "25", "支行员工"

    id = models.BigAutoField(primary_key=True)
    user_id = models.BigIntegerField("用户ID")
    org_id = models.BigIntegerField("机构ID")

    credit_employee_no = models.CharField("贷系统员工编号", max_length=32, null=True, blank=True)
    team_member_no = models.CharField("团队成员编号", max_length=32, null=True, blank=True)
    team_org_code = models.CharField("团队机构编码", max_length=32, null=True, blank=True)
    line_code = models.CharField("所属条线编码", max_length=32, null=True, blank=True)
    employee_level = models.CharField(
        "员工级别编码",
        max_length=2,
        choices=EmployeeLevel.choices,
        null=True,
        blank=True,
    )
    is_customer_manager = models.BooleanField("是否客户经理", default=False)
    position_name = models.CharField("岗位名称", max_length=64, null=True, blank=True)
    is_primary = models.BooleanField("是否主归属", default=False)
    status = models.CharField(
        "状态",
        max_length=2,
        choices=Status.choices,
        default=Status.NORMAL,
    )
    start_date = models.DateField("生效日期", null=True, blank=True)
    end_date = models.DateField("失效日期", null=True, blank=True)
    team_name = models.CharField("团队名称", max_length=64, null=True, blank=True)
    remark = models.CharField("备注", max_length=255, null=True, blank=True)
    class Meta:
        db_table = "shenzhen_user_org_rel"
        managed = False
        verbose_name = "用户机构关系"
        verbose_name_plural = "用户机构关系"
        unique_together = (("user_id", "org_id"),)
