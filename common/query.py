from django.db.models import QuerySet
from rest_framework.exceptions import ValidationError


def parse_bool_param(value, default=None):
    if value is None:
        return default

    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return True
    if normalized in {"0", "false", "no", "n"}:
        return False
    return default


def parse_optional_int_param(value, field_name):
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError({field_name: [f"{field_name}必须是整数"]}) from exc


def distinct_non_empty_values(queryset: QuerySet, field_name: str):
    return [
        item
        for item in queryset.exclude(**{f"{field_name}__isnull": True})
        .exclude(**{field_name: ""})
        .order_by(field_name)
        .values_list(field_name, flat=True)
        .distinct()
    ]
