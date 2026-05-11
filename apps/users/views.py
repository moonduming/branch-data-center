from django.contrib.auth import password_validation
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from common.permissions import IsAdminUserLevel
from ..organization.models import OrgUnit, UserOrgRelation
from .models import User
from .serializers import (
    LoginSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)

DEFAULT_RESET_PASSWORD = settings.DEFAULT_RESET_PASSWORD


def get_request_ip(request):
    """优先取代理透传 IP，不存在时回退到直连 IP"""
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def build_token_data(user):
    """构建 JWT token 数据"""
    access_token = AccessToken.for_user(user)
    return {
        "access": str(access_token),
        "expires_in": int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()),
    }


def update_login_info(user, request):
    """更新用户登录信息"""
    now = timezone.now()
    user.last_login = now
    user.last_login_ip = get_request_ip(request)
    user.save(update_fields=["last_login", "last_login_ip", "updated_at"])


def build_user_org_map(users):
    user_list = list(users)
    user_ids = [user.id for user in user_list if getattr(user, "id", None) is not None]
    result = {user_id: [] for user_id in user_ids}
    if not user_ids:
        return result

    relations = list(
        UserOrgRelation.objects.filter(
            user_id__in=user_ids,
            status=UserOrgRelation.Status.NORMAL,
        ).values("user_id", "org_id", "is_primary")
    )
    org_ids = {relation["org_id"] for relation in relations if relation.get("org_id") is not None}
    org_map = {
        item["id"]: item
        for item in OrgUnit.objects.filter(id__in=org_ids).values("id", "org_code", "org_name", "org_type")
    }

    relations.sort(key=lambda item: (not item["is_primary"], item["org_id"]))
    for relation in relations:
        org = org_map.get(relation["org_id"])
        if not org:
            continue
        result.setdefault(relation["user_id"], []).append(
            {
                "org_id": org["id"],
                "org_code": org["org_code"],
                "org_name": org["org_name"],
                "org_type": org["org_type"],
                "is_primary": relation["is_primary"],
            }
        )
    return result


def serialize_user(user, base_context=None):
    context = dict(base_context or {})
    context["user_org_map"] = build_user_org_map([user])
    return UserSerializer(user, context=context).data


def serialize_users(users, base_context=None):
    user_list = list(users)
    context = dict(base_context or {})
    context["user_org_map"] = build_user_org_map(user_list)
    return UserSerializer(user_list, many=True, context=context).data


def normalize_choice_value(raw_value, choices):
    if raw_value in (None, ""):
        return None

    value = str(raw_value).strip()
    for choice_value, choice_label in choices:
        if value in (choice_value, choice_label):
            return choice_value
    return value


def build_auth_response(user, include_token=False, auto_login=False):
    """构建认证响应数据"""
    data = {
        "logged_in": True,
        "auto_login": auto_login,
        "user": serialize_user(user),
    }
    if include_token:
        data["token"] = build_token_data(user)
    return data


def success_response(message, data=None, status_code=status.HTTP_200_OK):
    return Response(
        {
            "message": message,
            "data": data,
        },
        status=status_code,
    )


class LoginView(APIView):
    """用户登录视图"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        update_login_info(user, request)

        return success_response("登录成功", build_auth_response(user, include_token=True))


class AuthStatusView(APIView):
    """获取认证状态视图"""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if request.user and request.user.is_authenticated:
            return success_response("当前已登录", build_auth_response(request.user))

        request_ip = get_request_ip(request)
        user = User.objects.filter(bind_ip=request_ip, user_status=User.Status.NORMAL).first()
        if not user:
            return success_response(
                "未登录",
                {
                    "logged_in": False,
                    "auto_login": False,
                    "request_ip": request_ip,
                },
                status.HTTP_401_UNAUTHORIZED,
            )

        update_login_info(user, request)
        return success_response(
            "IP匹配成功，已自动登录",
            build_auth_response(user, include_token=True, auto_login=True),
        )


class UserListCreateView(generics.ListCreateAPIView):
    """用户列表和创建视图"""
    queryset = User.objects.all().order_by("-created_at", "-id")
    permission_classes = [IsAdminUserLevel]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return UserCreateSerializer
        return UserSerializer

    def get_queryset(self):
        queryset = User.objects.all().order_by("-created_at", "-id")

        username = (self.request.query_params.get("username") or "").strip()
        if username:
            queryset = queryset.filter(username__icontains=username)

        full_name = (self.request.query_params.get("full_name") or "").strip()
        if full_name:
            queryset = queryset.filter(full_name__icontains=full_name)

        user_status = normalize_choice_value(self.request.query_params.get("user_status"), User.Status.choices)
        if user_status:
            queryset = queryset.filter(user_status=user_status)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            return self.get_paginated_response(serialize_users(page, self.get_serializer_context()))

        return success_response("查询成功", serialize_users(queryset, self.get_serializer_context()))

    def perform_create(self, serializer):
        serializer.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return success_response("创建成功", serialize_user(serializer.instance, self.get_serializer_context()), status.HTTP_201_CREATED)


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """用户详情视图"""
    queryset = User.objects.all()
    permission_classes = [IsAdminUserLevel]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return UserUpdateSerializer
        return UserSerializer

    def perform_update(self, serializer):
        serializer.save()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return success_response("查询成功", serialize_user(instance, self.get_serializer_context()))

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return success_response("更新成功", serialize_user(serializer.instance, self.get_serializer_context()))

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if UserOrgRelation.objects.filter(user_id=instance.id).exists():
            return success_response(
                "删除失败",
                {"user_id": ["当前用户已被用户机构关系数据引用，请先删除关系表中的对应数据后再删除用户"]},
                status.HTTP_400_BAD_REQUEST,
            )
        self.perform_destroy(instance)
        return success_response("删除成功", None)


class ChangePasswordView(APIView):
    """修改密码视图"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if not old_password:
            return success_response("参数校验失败", {"old_password": ["原密码不能为空"]}, status.HTTP_400_BAD_REQUEST)

        if not new_password:
            return success_response("参数校验失败", {"new_password": ["新密码不能为空"]}, status.HTTP_400_BAD_REQUEST)

        if not confirm_password:
            return success_response("参数校验失败", {"confirm_password": ["确认密码不能为空"]}, status.HTTP_400_BAD_REQUEST)

        if not user.check_password(old_password):
            return success_response("原密码错误", {"old_password": ["原密码错误"]}, status.HTTP_400_BAD_REQUEST)
        if new_password != confirm_password:
            return success_response("参数校验失败", {"confirm_password": ["两次输入的新密码不一致"]}, status.HTTP_400_BAD_REQUEST)
        if old_password == new_password:
            return success_response("参数校验失败", {"new_password": ["新密码不能与原密码相同"]}, status.HTTP_400_BAD_REQUEST)

        try:
            password_validation.validate_password(new_password, user)
        except DjangoValidationError as exc:
            return success_response("参数校验失败", {"new_password": list(exc.messages)}, status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save(update_fields=["password", "updated_at"])

        return success_response("密码修改成功，请重新登录", None)


class ResetUserPasswordView(APIView):
    """管理员重置用户密码视图"""
    permission_classes = [IsAdminUserLevel]

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.set_password(DEFAULT_RESET_PASSWORD)
        user.save(update_fields=["password", "updated_at"])
        return success_response(f"密码重置成功，新密码为{DEFAULT_RESET_PASSWORD}", None)
