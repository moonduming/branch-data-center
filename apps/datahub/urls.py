from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AutoLoadDataBackupTriggerView,
    DataImportLogView,
    HeadOfficeImportTriggerView,
    IndicatorOptionView,
    OrgOptionView,
    ParentIndicatorOptionView,
    PerfIndicatorDashboardView,
    PerfIndicatorRuleViewSet,
    PerfIndicatorViewSet,
    ResultImportPostProfitTriggerView,
    ResultImportTriggerView,
)


router = DefaultRouter()
router.register('indicators', PerfIndicatorViewSet, basename='indicator')
router.register('indicator-rules', PerfIndicatorRuleViewSet, basename='indicator-rule')

urlpatterns = [
    path('dashboard/', PerfIndicatorDashboardView.as_view(), name='indicator-dashboard'),
    path('imports/logs/', DataImportLogView.as_view(), name='data-import-log-list'),
    path('imports/backup/trigger/', AutoLoadDataBackupTriggerView.as_view(), name='data-backup-trigger'),
    path('imports/head-office/trigger/', HeadOfficeImportTriggerView.as_view(), name='head-office-import-trigger'),
    path('imports/result/trigger/', ResultImportTriggerView.as_view(), name='result-import-trigger'),
    path(
        'imports/result/post-profit/trigger/',
        ResultImportPostProfitTriggerView.as_view(),
        name='result-import-post-profit-trigger',
    ),
    path('org-options/', OrgOptionView.as_view(), name='org-options'),
    path('parent-indicator-options/', ParentIndicatorOptionView.as_view(), name='parent-indicator-options'),
    path('indicator-options/', IndicatorOptionView.as_view(), name='indicator-options'),
] + router.urls
