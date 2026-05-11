from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    NodeAssigneeRuleOptionView,
    NodeDefOptionView,
    ProcessDefOptionView,
    TransitionDefOptionView,
    WfInstanceViewSet,
    WfNodeAssigneeRuleViewSet,
    WfNodeDefViewSet,
    WfProcessDefViewSet,
    WfTaskLogViewSet,
    WfTaskViewSet,
    WfTransitionDefViewSet,
    WfWorkItemViewSet,
    NodeAvailableActionView
)


router = DefaultRouter()
router.register('process-defs', WfProcessDefViewSet, basename='workflow-process-def')
router.register('node-defs', WfNodeDefViewSet, basename='workflow-node-def')
router.register('transition-defs', WfTransitionDefViewSet, basename='workflow-transition-def')
router.register('node-assignee-rules', WfNodeAssigneeRuleViewSet, basename='workflow-node-assignee-rule')
router.register('instances', WfInstanceViewSet, basename='workflow-instance')
router.register('tasks', WfTaskViewSet, basename='workflow-task')
router.register('work-items', WfWorkItemViewSet, basename='workflow-work-item')
router.register('task-logs', WfTaskLogViewSet, basename='workflow-task-log')

urlpatterns = [
    path('process-def-options/', ProcessDefOptionView.as_view(), name='workflow-process-def-options'),
    path('node-def-options/', NodeDefOptionView.as_view(), name='workflow-node-def-options'),
    path('transition-def-options/', TransitionDefOptionView.as_view(), name='workflow-transition-def-options'),
    path('node-available-actions/', NodeAvailableActionView.as_view(), name='workflow-node-available-actions'),
    path('node-assignee-rule-options/', NodeAssigneeRuleOptionView.as_view(), name='workflow-node-assignee-rule-options'),
] + router.urls
