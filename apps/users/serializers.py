from django.contrib.auth import authenticate, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from django.conf import settings
from rest_framework import serializers

from common.serializers import IgnoreExtraFieldsMixin

from .models import User


class UserSerializer(serializers.ModelSerializer):
    user_status = serializers.SerializerMethodField()
    user_status_code = serializers.CharField(source="user_status", read_only=True)
    user_level = serializers.SerializerMethodField()
    user_level_code = serializers.CharField(source="user_level", read_only=True)
    orgs = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "full_name",
            "user_status",
            "user_status_code",
            "user_level",
            "user_level_code",
            "orgs",
            "bind_ip",
            "last_login",
            "last_login_ip",
            "created_at",
            "updated_at",
        ]

    def get_user_status(self, obj):
        return obj.get_user_status_display()

    def get_user_level(self, obj):
        return obj.get_user_level_display()

    def get_orgs(self, obj):
        return self.context.get("user_org_map", {}).get(obj.id, [])


class LoginSerializer(IgnoreExtraFieldsMixin, serializers.Serializer):
    # 登录参数校验
    username = serializers.CharField(max_length=32, allow_blank=False, trim_whitespace=True)
    password = serializers.CharField(write_only=True, allow_blank=False, trim_whitespace=False)

    default_error_messages = {
        "invalid_credentials": "用户名或密码错误",
        "invalid_status": "当前用户状态不可登录",
    }

    def validate(self, attrs):
        username = attrs["username"].strip()
        password = attrs["password"]

        user = authenticate(username=username, password=password)
        if not user:
            self.fail("invalid_credentials")

        if user.user_status != User.Status.NORMAL:
            self.fail("invalid_status")

        attrs["user"] = user
        attrs["username"] = username
        return attrs


class UserCreateSerializer(IgnoreExtraFieldsMixin, serializers.ModelSerializer):
    # 创建用户时明文密码只用于入参，不直接落库
    password = serializers.CharField(
        write_only=True, 
        required=False, 
        allow_blank=True, 
        min_length=8, 
        max_length=128, 
        trim_whitespace=False
    )
    drop_empty_fields = {"user_status", "user_level"}
    empty_to_none_fields = {"bind_ip"}

    class Meta:
        model = User
        fields = [
            "username",
            "password",
            "full_name",
            "user_status",
            "user_level",
            "bind_ip",
        ]
        extra_kwargs = {
            "bind_ip": {"required": False, "allow_null": True},
        }

    def validate_password(self, value):
        # 只有在显式传入 password 时才做校验
        if value:
            try:
                password_validation.validate_password(value)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(list(exc.messages)) from exc
        return value

    def create(self, validated_data):
        password = validated_data.pop("password", None)

        # 未传 password，使用默认密码且不做校验
        if not password:
            password = settings.DEFAULT_RESET_PASSWORD

        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(IgnoreExtraFieldsMixin, serializers.ModelSerializer):
    drop_empty_fields = {"user_status", "user_level"}
    empty_to_none_fields = {"bind_ip"}

    class Meta:
        model = User
        fields = [
            "username",
            "full_name",
            "user_status",
            "user_level",
            "bind_ip",
        ]
        extra_kwargs = {
            "bind_ip": {"required": False, "allow_null": True},
        }
