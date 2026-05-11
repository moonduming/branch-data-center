from django.urls import path

from .views import (
    AuthStatusView,
    ChangePasswordView,
    LoginView,
    ResetUserPasswordView,
    UserDetailView,
    UserListCreateView,
)


urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("auth/status/", AuthStatusView.as_view(), name="auth-status"),
    path("users/change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("users/", UserListCreateView.as_view(), name="user-list-create"),
    path("users/<int:pk>/reset-password/", ResetUserPasswordView.as_view(), name="user-reset-password"),
    path("users/<int:pk>/", UserDetailView.as_view(), name="user-detail"),
]
