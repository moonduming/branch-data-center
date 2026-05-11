from django.db.models import Q
from rest_framework import status, viewsets

from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import permissions

from common.permissions import IsAdminUserLevel
from apps.users.models import User

from .models import OrgUnit, UserOrgRelation
from .serializers import OrgUnitSerializer, UserOrgRelationSerializer


def normalize_choice_value(raw_value, choices):
    if raw_value in (None, ""):
        return None

    value = str(raw_value).strip()
    for choice_value, choice_label in choices:
        if value in (choice_value, choice_label):
            return choice_value
    return value


def get_search_value(request):
    for key in ("keyword", "value", "query"):
        value = (request.query_params.get(key) or "").strip()
        if value:
            return value
    return ""


def success_response(data, message="查询成功", status_code=status.HTTP_200_OK):
    return Response({"message": message, "data": data}, status=status_code)


class UserOptionListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        keyword = get_search_value(request)
        org_id = (request.query_params.get("org_id") or "").strip()
        queryset = User.objects.all().order_by("username", "id")
        if org_id:
            user_ids = UserOrgRelation.objects.filter(
                org_id=org_id,
                status=UserOrgRelation.Status.NORMAL,
            ).values_list("user_id", flat=True)
            queryset = queryset.filter(id__in=user_ids)
        if keyword:
            queryset = queryset.filter(Q(username__icontains=keyword) | Q(full_name__icontains=keyword))

        data = list(queryset.values("id", "full_name", "username"))
        return success_response(
            [{"user_id": item["id"], "user_name": item["full_name"], "user_code": item["username"]} for item in data]
        )


class OrgUnitOptionListView(APIView):
    permission_classes = [IsAdminUserLevel]

    def get(self, request):
        keyword = get_search_value(request)
        queryset = OrgUnit.objects.all().order_by("display_order", "id")
        if keyword:
            queryset = queryset.filter(Q(org_code__icontains=keyword) | Q(org_name__icontains=keyword))

        data = list(queryset.values("id", "org_name", "org_code"))
        return success_response(
            [{"org_id": item["id"], "org_name": item["org_name"], "org_code": item["org_code"]} for item in data]
        )


class OrgTypeOptionListView(APIView):
    permission_classes = [IsAdminUserLevel]

    def get(self, request):
        data = [{"org_type": value, "org_type_label": label} for value, label in OrgUnit.OrgType.choices]
        return success_response(data)


class OrgUnitViewSet(viewsets.ModelViewSet):
    queryset = OrgUnit.objects.all().order_by("display_order", "id")
    serializer_class = OrgUnitSerializer
    permission_classes = [IsAdminUserLevel]

    def get_queryset(self):
        queryset = OrgUnit.objects.all().order_by("display_order", "id")

        org_name = (self.request.query_params.get("org_name") or "").strip()
        if org_name:
            queryset = queryset.filter(org_name__icontains=org_name)

        status_value = normalize_choice_value(self.request.query_params.get("status"), OrgUnit.Status.choices)
        if status_value:
            queryset = queryset.filter(status=status_value)

        return queryset

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if UserOrgRelation.objects.filter(org_id=instance.id).exists():
            raise ValidationError({"message": "当前机构已被用户机构关系数据引用，请先删除关系表中的对应数据后再删除机构"})
        return super().destroy(request, *args, **kwargs)


class UserOrgRelationViewSet(viewsets.ModelViewSet):
    serializer_class = UserOrgRelationSerializer
    permission_classes = [IsAdminUserLevel]

    def _attach_related_info(self, objects):
        relations = list(objects)
        if not relations:
            return relations

        user_ids = {relation.user_id for relation in relations if relation.user_id is not None}
        org_ids = {relation.org_id for relation in relations if relation.org_id is not None}

        user_map = {
            item["id"]: item
            for item in User.objects.filter(id__in=user_ids).values("id", "username", "full_name")
        }
        org_map = {
            item["id"]: item
            for item in OrgUnit.objects.filter(id__in=org_ids).values("id", "org_code", "org_name")
        }

        for relation in relations:
            user = user_map.get(relation.user_id)
            org = org_map.get(relation.org_id)
            relation.username = user["username"] if user else None
            relation.full_name = user["full_name"] if user else None
            relation.org_code = org["org_code"] if org else None
            relation.org_name = org["org_name"] if org else None

        return relations

    def _validate_related_objects(self, validated_data, instance=None):
        user_id = validated_data.get("user_id")
        org_id = validated_data.get("org_id")

        if user_id is None and instance is not None:
            user_id = instance.user_id
        if org_id is None and instance is not None:
            org_id = instance.org_id

        if user_id is not None and not User.objects.filter(id=user_id).exists():
            raise ValidationError({"user_id": "用户不存在"})

        if org_id is not None and not OrgUnit.objects.filter(id=org_id).exists():
            raise ValidationError({"org_id": "机构不存在"})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self._validate_related_objects(serializer.validated_data)
        self.perform_create(serializer)
        self._attach_related_info([serializer.instance])
        serializer = self.get_serializer(serializer.instance)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self._validate_related_objects(serializer.validated_data, instance=instance)
        self.perform_update(serializer)
        self._attach_related_info([serializer.instance])
        serializer = self.get_serializer(serializer.instance)

        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            self._attach_related_info(page)
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        relations = self._attach_related_info(queryset)
        serializer = self.get_serializer(relations, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        self._attach_related_info([instance])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_queryset(self):
        queryset = UserOrgRelation.objects.all().order_by("-id")

        org_name = (self.request.query_params.get("org_name") or "").strip()
        if org_name:
            org_ids = OrgUnit.objects.filter(org_name__icontains=org_name).values_list("id", flat=True)
            queryset = queryset.filter(org_id__in=org_ids)

        employee = (self.request.query_params.get("employee") or "").strip()
        if employee:
            user_ids = User.objects.filter(
                Q(username__icontains=employee) | Q(full_name__icontains=employee)
            ).values_list("id", flat=True)
            queryset = queryset.filter(user_id__in=user_ids)

        status_value = normalize_choice_value(self.request.query_params.get("status"), UserOrgRelation.Status.choices)
        if status_value:
            queryset = queryset.filter(status=status_value)

        return queryset
