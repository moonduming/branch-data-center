from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    OrgTypeOptionListView,
    OrgUnitOptionListView,
    OrgUnitViewSet,
    UserOptionListView,
    UserOrgRelationViewSet,
)


router = DefaultRouter()
router.register("org-units", OrgUnitViewSet, basename="org-unit")
router.register("user-org-relations", UserOrgRelationViewSet, basename="user-org-relation")

urlpatterns = [
    path("options/users/", UserOptionListView.as_view(), name="organization-user-options"),
    path("options/org-units/", OrgUnitOptionListView.as_view(), name="organization-org-options"),
    path("options/org-types/", OrgTypeOptionListView.as_view(), name="organization-org-type-options"),
]
urlpatterns += router.urls
