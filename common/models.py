from django.db import models


class ManualTableTimestampMixin(models.Model):
    """为手工维护的表统一补充 Django 侧时间戳行为。"""

    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        abstract = True
