from unittest.mock import Mock, call, patch

from django.test import SimpleTestCase
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.users.models import User
from apps.organization.models import OrgUnit, UserOrgRelation
from apps.organization.serializers import OrgUnitSerializer, UserOrgRelationSerializer
from apps.organization.views import (
    OrgTypeOptionListView,
    OrgUnitOptionListView,
    OrgUnitViewSet,
    UserOptionListView,
    UserOrgRelationViewSet,
)


class OrgUnitSerializerTests(SimpleTestCase):
    def test_org_unit_serializer_exposes_label_fields(self):
        instance = OrgUnit(
            id=1,
            org_code="44000001",
            org_name="深圳分行",
            org_type=OrgUnit.OrgType.BRANCH,
            status=OrgUnit.Status.NORMAL,
        )

        data = OrgUnitSerializer(instance).data

        self.assertEqual(data["org_type"], OrgUnit.OrgType.BRANCH)
        self.assertEqual(data["org_type_label"], "分行")
        self.assertEqual(data["status"], OrgUnit.Status.NORMAL)
        self.assertEqual(data["status_label"], "正常")


class UserOrgRelationSerializerTests(SimpleTestCase):
    def test_relation_serializer_exposes_status_label(self):
        instance = UserOrgRelation(
            id=1,
            user_id=10,
            org_id=20,
            team_name="零售一组",
            employee_level=UserOrgRelation.EmployeeLevel.DEPT_STAFF,
            status=UserOrgRelation.Status.INVALID,
        )
        instance.username = "10001"
        instance.full_name = "张三"
        instance.org_code = "44000001"
        instance.org_name = "深圳分行"

        data = UserOrgRelationSerializer(instance).data

        self.assertEqual(data["employee_level"], UserOrgRelation.EmployeeLevel.DEPT_STAFF)
        self.assertEqual(data["employee_level_label"], "部室员工")
        self.assertEqual(data["team_name"], "零售一组")
        self.assertEqual(data["status"], UserOrgRelation.Status.INVALID)
        self.assertEqual(data["status_label"], "失效")


class OrgUnitViewSetQueryTests(SimpleTestCase):
    @patch("apps.organization.views.OrgUnit.objects.all")
    def test_get_queryset_supports_org_name_and_status_filters(self, mock_all):
        queryset = Mock()
        queryset.order_by.return_value = queryset
        queryset.filter.return_value = queryset
        mock_all.return_value = queryset

        request = APIRequestFactory().get(
            "/api/organization/org-units/",
            {"org_name": "深圳", "status": "正常"},
        )
        view = OrgUnitViewSet()
        view.request = Request(request)

        result = view.get_queryset()

        self.assertIs(result, queryset)
        queryset.filter.assert_has_calls(
            [
                call(org_name__icontains="深圳"),
                call(status=OrgUnit.Status.NORMAL),
            ]
        )


class UserOrgRelationViewSetQueryTests(SimpleTestCase):
    @patch("apps.organization.views.OrgUnit.objects.filter")
    @patch("apps.organization.views.User.objects.filter")
    @patch("apps.organization.views.UserOrgRelation.objects.all")
    def test_get_queryset_supports_org_employee_and_status_filters(
        self,
        mock_relation_all,
        mock_user_filter,
        mock_org_filter,
    ):
        relation_queryset = Mock()
        relation_queryset.order_by.return_value = relation_queryset
        relation_queryset.filter.return_value = relation_queryset
        mock_relation_all.return_value = relation_queryset

        org_queryset = Mock()
        org_queryset.values_list.return_value = [20]
        mock_org_filter.return_value = org_queryset

        user_queryset = Mock()
        user_queryset.values_list.return_value = [10]
        mock_user_filter.return_value = user_queryset

        request = APIRequestFactory().get(
            "/api/organization/user-org-relations/",
            {"org_name": "深圳", "employee": "张三", "status": "失效"},
        )
        view = UserOrgRelationViewSet()
        view.request = Request(request)

        result = view.get_queryset()

        self.assertIs(result, relation_queryset)
        mock_org_filter.assert_called_once_with(org_name__icontains="深圳")
        self.assertEqual(mock_user_filter.call_count, 1)
        relation_queryset.filter.assert_has_calls(
            [
                call(org_id__in=[20]),
                call(user_id__in=[10]),
                call(status=UserOrgRelation.Status.INVALID),
            ]
        )


class OptionListViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.admin_user = User(id=1, username="admin", full_name="管理员", user_level=User.Level.ADMIN)

    @patch("apps.organization.views.UserOrgRelation.objects.filter")
    @patch("apps.organization.views.User.objects.all")
    def test_user_option_list_supports_keyword_search_and_org_filter(self, mock_all, mock_relation_filter):
        queryset = Mock()
        queryset.order_by.return_value = queryset
        queryset.filter.return_value = queryset
        queryset.values.return_value = [{"id": 10, "full_name": "张三", "username": "10001"}]
        mock_all.return_value = queryset
        mock_relation_filter.return_value.values_list.return_value = [10]

        request = self.factory.get("/api/organization/options/users/", {"keyword": "10001", "org_id": 20})
        force_authenticate(request, user=self.admin_user)

        response = UserOptionListView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        mock_relation_filter.assert_called_once_with(org_id="20", status=UserOrgRelation.Status.NORMAL)
        queryset.filter.assert_any_call(id__in=[10])
        self.assertEqual(queryset.filter.call_count, 2)
        self.assertEqual(response.data["data"], [{"user_id": 10, "user_name": "张三", "user_code": "10001"}])

    @patch("apps.organization.views.OrgUnit.objects.all")
    def test_org_option_list_supports_keyword_search(self, mock_all):
        queryset = Mock()
        queryset.order_by.return_value = queryset
        queryset.filter.return_value = queryset
        queryset.values.return_value = [{"id": 20, "org_name": "深圳分行", "org_code": "4400"}]
        mock_all.return_value = queryset

        request = self.factory.get("/api/organization/options/org-units/", {"value": "4400"})
        force_authenticate(request, user=self.admin_user)

        response = OrgUnitOptionListView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        queryset.filter.assert_called_once()
        self.assertEqual(response.data["data"], [{"org_id": 20, "org_name": "深圳分行", "org_code": "4400"}])

    def test_org_type_option_list_returns_all_choices(self):
        request = self.factory.get("/api/organization/options/org-types/")
        force_authenticate(request, user=self.admin_user)

        response = OrgTypeOptionListView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn({"org_type": "00", "org_type_label": "分行"}, response.data["data"])
