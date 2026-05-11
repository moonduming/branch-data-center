from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ShenzhenPropStatusViewSet, OrgOptionView


router = DefaultRouter()
router.register('prop-statuses', ShenzhenPropStatusViewSet, basename='performance-prop-status')

urlpatterns = [
path('org-options/', OrgOptionView.as_view(), name='org-options'),
] + router.urls
