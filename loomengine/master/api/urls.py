from django.conf.urls import include, url
from rest_framework import routers

import api.views

router = routers.DefaultRouter()

router.register('data-objects', api.views.DataObjectViewSet, base_name='DataObject')
router.register('files', api.views.FileDataObjectViewSet, base_name='File')
router.register('data-trees', api.views.DataTreeViewSet, base_name='DataTree')
router.register('file-resources', api.views.FileResourceViewSet, base_name='FileResources')
router.register('tasks',
                api.views.TaskViewSet,
                base_name='Task')
router.register('task-attempts',
                api.views.TaskAttemptViewSet,
                base_name='TaskAttempt')
router.register('task-attempt-outputs',
                api.views.TaskAttemptOutputViewSet,
                base_name='TaskAttemptOutput')
router.register('task-attempt-log-files',
                api.views.TaskAttemptLogFileViewSet,
                base_name='TaskAttemptOutputLogFile')
router.register('task-attempt-errors',
                api.views.TaskAttemptErrorViewSet,
                base_name='TaskAttemptError')
router.register('templates',
                api.views.TemplateViewSet,
                base_name='Template')
router.register('runs',
                api.views.RunViewSet,
                base_name='Run')
router.register('run-requests',
                api.views.RunRequestViewSet,
                base_name='RunRequest')

# file_provenance_detail = api.views.FileProvenanceViewSet.as_view({'get':'retrieve'})

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^status/$', api.views.status),
    url(r'^info/$', api.views.info),
    url(r'^filemanager-settings/$', api.views.filemanager_settings),
    #    url(r'^files/(?P<pk>[a-zA-Z0-9]+)/provenance/$', file_provenance_detail, name='file_provenance_detail'),
]
