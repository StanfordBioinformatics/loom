from django.conf import settings
from django.conf.urls import include, url
from rest_framework import routers
from rest_framework_swagger.views import get_swagger_view
from api import get_setting

import api.views


router = routers.DefaultRouter()

router.register('data-objects',
                api.views.DataObjectViewSet,
                base_name='data-object')
router.register('data-nodes',
                api.views.DataNodeViewSet,
                base_name='data-node')
router.register('tasks',
                api.views.TaskViewSet,
                base_name='task')
router.register('task-attempts',
                api.views.TaskAttemptViewSet,
                base_name='task-attempt')
router.register('outputs',
                api.views.TaskAttemptOutputViewSet,
                base_name='task-attempt-output')
router.register('log-files',
                api.views.TaskAttemptLogFileViewSet,
                base_name='task-attempt-log-file')
router.register('templates',
                api.views.TemplateViewSet,
                base_name='template')
router.register('runs',
                api.views.RunViewSet,
                base_name='run')
router.register('data-tags',
                api.views.DataTagViewSet,
                base_name='data-tag')
router.register('data-labels',
                api.views.DataLabelViewSet,
                base_name='data-label')
router.register('template-tags',
                api.views.TemplateTagViewSet,
                base_name='template-tag')
router.register('template-labels',
                api.views.TemplateLabelViewSet,
                base_name='template-label')
router.register('run-tags',
                api.views.RunTagViewSet,
                base_name='run-tag')
router.register('run-labels',
                api.views.RunLabelViewSet,
                base_name='run-label')
router.register('users',
                api.views.UserViewSet,
                base_name='user')

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^status/$', api.views.status),
    url(r'^info/$', api.views.info),
    url(r'^auth-status/$', api.views.auth_status),
    url(r'^storage-settings/$', api.views.StorageSettingsView.as_view()),
    url(r'^doc/$', get_swagger_view(title='Loom API')),
]

if get_setting('LOGIN_REQUIRED'):
    urlpatterns.extend([
        url(r'^auth/$', api.views.AuthView.as_view()),
        url(r'^tokens/$', api.views.TokenView.as_view()),
    ])

if settings.DEBUG:
    # This view is for testing response to a server error, e.g. where
    # server errors are logged.
    urlpatterns.extend([
        url('^error/$', api.views.raise_server_error),
    ])
