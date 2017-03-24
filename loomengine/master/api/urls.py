from django.conf import settings
from django.conf.urls import include, url
from rest_framework import routers

import api.views

router = routers.DefaultRouter()

router.register('data-objects', api.views.DataObjectViewSet, base_name='data-object')
router.register('files', api.views.FileDataObjectViewSet, base_name='file')
router.register('data-trees', api.views.DataTreeViewSet, base_name='data-tree')
router.register('file-resources', api.views.FileResourceViewSet, base_name='file-resource')
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
router.register('templates',
                api.views.TemplateViewSet,
                base_name='template')
router.register('runs',
                api.views.RunViewSet,
                base_name='run')
router.register('run-requests',
                api.views.RunRequestViewSet,
                base_name='run-request')

# file_provenance_detail = api.views.FileProvenanceViewSet.as_view({'get':'retrieve'})

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^status/$', api.views.status),
    url(r'^info/$', api.views.info),
    url(r'^filemanager-settings/$', api.views.filemanager_settings),
    #    url(r'^files/(?P<pk>[a-zA-Z0-9]+)/provenance/$', file_provenance_detail, name='file_provenance_detail'),
]

if settings.DEBUG:
    urlpatterns.append(
        url('^error/$', api.views.raise_server_error)
    )
