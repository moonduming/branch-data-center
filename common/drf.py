import logging
import time
from collections.abc import Mapping, Sequence

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer


GENERIC_ERROR_MESSAGES = {"error", "参数校验失败", "删除失败", "创建失败", "更新失败"}


def _flatten_error_messages(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        messages = []
        for item in value.values():
            messages.extend(_flatten_error_messages(item))
        return messages
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        messages = []
        for item in value:
            messages.extend(_flatten_error_messages(item))
        return messages
    return [str(value)]


def _extract_message_and_errors(data):
    if not isinstance(data, Mapping):
        return str(data), None, None

    message = data.get("message")
    errors = data.get("data")
    error_code = data.get("error_code") or data.get("code")

    if "detail" in data:
        detail = data.get("detail")
        detail_message = str(detail)
        if error_code == "token_not_valid":
            return "登录已失效，请重新登录", data, "token_expired"
        if error_code == "not_authenticated":
            return "未登录或登录已失效", data, "not_authenticated"
        if error_code == "authentication_failed":
            return detail_message, data, "authentication_failed"
        return detail_message, data, error_code

    if message is not None:
        flattened = _flatten_error_messages(errors)
        if flattened and str(message) in GENERIC_ERROR_MESSAGES:
            return flattened[0], errors, error_code
        return str(message), errors, error_code

    flattened = _flatten_error_messages(data)
    if flattened:
        return flattened[0], data, error_code

    return "请求失败", data, error_code


def normalize_error_payload(data):
    message, errors, error_code = _extract_message_and_errors(data)
    payload = {"message": message}
    if error_code:
        payload["error_code"] = error_code
    if errors not in (None, {}, [], ()):
        payload["errors"] = errors
    return payload


def custom_exception_handler(exc, context):
    # 导入放在函数内部，避免循环导入
    from rest_framework.views import exception_handler as drf_exception_handler
    response = drf_exception_handler(exc, context)
    if response is None:
        return response

    response.data = normalize_error_payload(response.data)
    return response


class CountDataPagination(PageNumberPagination):
    """
    统一分页返回格式:
    {
      "message": "查询成功",
      "data": {
        "count": <总数>,
        "data": [ ... ]
      }
    }
    """
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "message": "查询成功",
            "data": {
                "count": self.page.paginator.count,
                "data": data,
            },
        })


class MessageDataJSONRenderer(JSONRenderer):
    """
    统一响应格式：
    - 业务成功响应保持 {message, data}
    - 分页响应保持 {message, data: {count, data}}
    - 其他成功响应兜底包装为 {message: "ok", data: ...}
    - 错误响应统一为 {message, error_code?, errors?}
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response") if renderer_context else None
        status_code = getattr(response, "status_code", 200)

        if data is None:
            return super().render(data, accepted_media_type, renderer_context)

        # DRF 原生分页结构
        if isinstance(data, dict) and {"count", "results"}.issubset(data.keys()):
            data = {
                "message": "查询成功",
                "data": {
                    "count": data.get("count", 0),
                    "data": data.get("results", []),
                },
            }
            return super().render(data, accepted_media_type, renderer_context)

        # 已经是业务约定的成功响应或分页响应，不再重复包装
        if isinstance(data, dict) and {"message", "data"}.issubset(data.keys()) and status_code < 400:
            return super().render(data, accepted_media_type, renderer_context)

        if status_code >= 400:
            if isinstance(data, dict) and "message" in data and "data" not in data:
                return super().render(data, accepted_media_type, renderer_context)
            return super().render(normalize_error_payload(data), accepted_media_type, renderer_context)

        # 非分页成功响应统一
        wrapped = {"message": "ok", "data": data}
        return super().render(wrapped, accepted_media_type, renderer_context)

