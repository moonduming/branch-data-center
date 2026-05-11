from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.users.models import User
from apps.users.serializers import UserSerializer
from apps.users.views import ResetUserPasswordView, build_user_org_map


class UserSerializerTests(SimpleTestCase):
    def test_user_serializer_maps_choice_labels_and_orgs(self):
        user = User(
            id=1,
            username="10001",
            full_name="张三",
            user_status=User.Status.NORMAL,
            user_level=User.Level.ADMIN,
        )

        serializer = UserSerializer(
            user,
            context={
                "user_org_map": {
                    1: [
                        {
                            "org_id": 10,
                            "org_code": "44000001",
                            "org_name": "深圳分行",
                            "is_primary": True,
                        }
                    ]
                }
            },
        )

        self.assertEqual(serializer.data["user_status"], "正常")
        self.assertEqual(serializer.data["user_status_code"], User.Status.NORMAL)
        self.assertEqual(serializer.data["user_level"], "超级管理员")
        self.assertEqual(serializer.data["user_level_code"], User.Level.ADMIN)
        self.assertEqual(serializer.data["orgs"][0]["org_code"], "44000001")


class UserOrgMapTests(SimpleTestCase):
    @patch("apps.users.views.OrgUnit.objects.filter")
    @patch("apps.users.views.UserOrgRelation.objects.filter")
    def test_build_user_org_map_sorts_primary_org_first(self, mock_relation_filter, mock_org_filter):
        relation_queryset = Mock()
        relation_queryset.values.return_value = [
            {"user_id": 1, "org_id": 2, "is_primary": False},
            {"user_id": 1, "org_id": 1, "is_primary": True},
        ]
        mock_relation_filter.return_value = relation_queryset

        org_queryset = Mock()
        org_queryset.values.return_value = [
            {"id": 1, "org_code": "44000001", "org_name": "深圳分行"},
            {"id": 2, "org_code": "44000002", "org_name": "南山支行"},
        ]
        mock_org_filter.return_value = org_queryset

        user = User(id=1, username="10001", full_name="张三")
        org_map = build_user_org_map([user])

        self.assertEqual([item["org_id"] for item in org_map[1]], [1, 2])


class ResetPasswordViewTests(SimpleTestCase):
    def test_admin_can_reset_password(self):
        factory = APIRequestFactory()
        request = factory.post("/api/users/2/reset-password/")
        force_authenticate(request, user=User(id=1, username="admin", user_level=User.Level.ADMIN))

        target_user = Mock()
        target_user.set_password = Mock()
        target_user.save = Mock()

        with patch("apps.users.views.get_object_or_404", return_value=target_user):
            response = ResetUserPasswordView.as_view()(request, pk=2)

        self.assertEqual(response.status_code, 200)
        target_user.set_password.assert_called_once_with("123456")
        target_user.save.assert_called_once_with(update_fields=["password", "updated_at"])
