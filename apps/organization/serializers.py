from rest_framework import serializers

from common.serializers import IgnoreExtraFieldsMixin

from .models import OrgUnit, UserOrgRelation


class OrgUnitSerializer(IgnoreExtraFieldsMixin, serializers.ModelSerializer):
    org_type_label = serializers.CharField(source="get_org_type_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    drop_empty_fields = {"parent_id"}
    empty_to_none_fields = {
        "credit_org_code",
        "virtual_employee_no",
        "leader_employee_no",
        "manager_employee_no",
        "remark",
    }

    class Meta:
        model = OrgUnit
        fields = [
            "id",
            "org_code",
            "credit_org_code",
            "virtual_employee_no",
            "org_name",
            "org_type",
            "org_type_label",
            "is_assessment_dept",
            "leader_employee_no",
            "manager_employee_no",
            "display_order",
            "status",
            "status_label",
            "parent_id",
            "remark",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "credit_org_code": {"required": False, "allow_null": True, "allow_blank": True},
            "virtual_employee_no": {"required": False, "allow_null": True, "allow_blank": True},
            "leader_employee_no": {"required": False, "allow_null": True, "allow_blank": True},
            "manager_employee_no": {"required": False, "allow_null": True, "allow_blank": True},
            "parent_id": {"required": False, "allow_null": True},
            "remark": {"required": False, "allow_null": True, "allow_blank": True},
        }


class UserOrgRelationSerializer(IgnoreExtraFieldsMixin, serializers.ModelSerializer):
    user_id = serializers.IntegerField()
    org_id = serializers.IntegerField()
    username = serializers.CharField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    org_code = serializers.CharField(read_only=True)
    org_name = serializers.CharField(read_only=True)
    employee_level_label = serializers.CharField(source="get_employee_level_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    drop_empty_fields = {"user_id", "org_id", "employee_level", "status", "start_date", "end_date"}
    empty_to_none_fields = {
        "credit_employee_no",
        "team_member_no",
        "team_org_code",
        "team_name",
        "line_code",
        "position_name",
        "remark",
    }

    class Meta:
        model = UserOrgRelation
        fields = [
            "id",
            "user_id",
            "org_id",
            "username",
            "full_name",
            "org_code",
            "org_name",
            "credit_employee_no",
            "team_member_no",
            "team_org_code",
            "team_name",
            "line_code",
            "employee_level",
            "employee_level_label",
            "is_customer_manager",
            "position_name",
            "is_primary",
            "status",
            "status_label",
            "start_date",
            "end_date",
            "remark",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "username",
            "full_name",
            "org_code",
            "org_name",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "credit_employee_no": {"required": False, "allow_null": True, "allow_blank": True},
            "team_member_no": {"required": False, "allow_null": True, "allow_blank": True},
            "team_org_code": {"required": False, "allow_null": True, "allow_blank": True},
            "team_name": {"required": False, "allow_null": True, "allow_blank": True},
            "line_code": {"required": False, "allow_null": True, "allow_blank": True},
            "position_name": {"required": False, "allow_null": True, "allow_blank": True},
            "start_date": {"required": False, "allow_null": True},
            "end_date": {"required": False, "allow_null": True},
            "remark": {"required": False, "allow_null": True, "allow_blank": True},
        }
