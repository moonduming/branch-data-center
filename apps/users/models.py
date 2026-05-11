from django.contrib.auth.models import AbstractUser
from django.db import models

from common.models import ManualTableTimestampMixin


class User(ManualTableTimestampMixin, AbstractUser):
    # 移除不需要的默认字段，避免表结构复杂化
    first_name = None
    last_name = None
    email = None
    date_joined = None
    is_staff = None
    is_superuser = None
    groups = None
    user_permissions = None

    class Status(models.TextChoices):
        NORMAL = "01", "正常"
        PAUSED = "05", "暂停"
        LEFT = "09", "离职"

    class Level(models.TextChoices):
        NORMAL = "00", "普通用户"
        ADMIN = "99", "超级管理员"

    # 用户名直接作为员工编号使用
    username = models.CharField(
        "员工编号",
        max_length=32,
        unique=True,
        db_column="employee_no",
    )
    full_name = models.CharField("员工姓名", max_length=50, db_column="employee_name")
    user_status = models.CharField(
        "用户状态",
        max_length=2,
        choices=Status.choices,
        default=Status.NORMAL,
        db_column="user_status",
    )
    user_level = models.CharField(
        "用户级别",
        max_length=2,
        choices=Level.choices,
        default=Level.NORMAL,
        db_column="user_level",
    )
    last_login = models.DateTimeField(
        "最后登录时间",
        null=True,
        blank=True,
        db_column="last_login_time",
    )
    last_login_ip = models.GenericIPAddressField(
        "最后登录IP",
        null=True,
        blank=True,
        db_column="last_login_ip",
    )
    bind_ip = models.GenericIPAddressField(
        "绑定IP",
        null=True,
        blank=True,
        unique=True,
        db_column="bind_ip",
    )

    class Meta:
        db_table = "shenzhen_sys_user"
        managed = False
        verbose_name = "用户"
        verbose_name_plural = "用户"
