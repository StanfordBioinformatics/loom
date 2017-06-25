from django.conf import settings
from django.conf.urls import include, url
from rest_framework import routers
from rest_framework_swagger.views import get_swagger_view

import api.views

router = routers.DefaultRouter()

router.register('data-objects',
                api.views.DataObjectViewSet,
                base_name='data-object')
"""
router.register('tasks',
                api.views.TaskViewSet,
                base_name='task')
router.register('task-attempts',
                api.views.TaskAttemptViewSet,
                base_name='task-attempt')
router.register('task-attempt-outputs',
                api.views.TaskAttemptOutputViewSet,
                base_name='task-attempt-output')
router.register('task-attempt-log-files',
                api.views.TaskAttemptLogFileViewSet,
                base_name='task-attempt-log-file')
"""
router.register('templates',
                api.views.TemplateViewSet,
                base_name='template')
router.register('runs',
                api.views.RunViewSet,
                base_name='run')

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^status/$', api.views.status),
    url(r'^info/$', api.views.info),
    url(r'^filemanager-settings/$', api.views.filemanager_settings),
    url(r'^doc/$', get_swagger_view(title='Loom API')),
]

if settings.DEBUG:
    # This view is for testing response to a server error, e.g. where
    # server errors are logged.
    urlpatterns.append(
        url('^error/$', api.views.raise_server_error)
    )
