from django.conf.urls import patterns, include, url
from rest_framework import routers

from api import models
from api import views

router = routers.DefaultRouter()

router.register('abstract-workflows', views.AbstractWorkflowViewSet, base_name='Workflow')
router.register('imported-workflows', views.ImportedWorkflowViewSet, base_name='ImportedWorkflow')
router.register('files', views.FileDataObjectViewSet, base_name='FileDataObject')
router.register('imported-files', views.ImportedFileDataObjectViewSet, base_name='ImportedFile')
router.register('result-files', views.ResultFileDataObjectViewSet, base_name='ResultFile')
router.register('log-files', views.LogFileDataObjectViewSet, base_name='LogFile')
router.register('run-requests', views.RunRequestViewSet, base_name='RunRequest')
router.register('abstract-workflow-runs', views.AbstractWorkflowRunViewSet)
router.register('task-runs', views.TaskRunViewSet)
router.register('task-run-attempts', views.TaskRunAttemptViewSet)
router.register('task-run-attempt-outputs', views.TaskRunAttemptOutputViewSet)
router.register('file-imports', views.FileImportViewSet)
router.register('file-locations', views.FileLocationViewSet)

file_provenance_detail = views.FileProvenanceViewSet.as_view({'get':'retrieve'})

urlpatterns = patterns(
    '',
    url(r'^', include(router.urls)),
    url(r'^files/(?P<pk>[a-zA-Z0-9]+)/provenance/$', file_provenance_detail, name='file_provenance_detail'),
    url(r'^status/$', 'api.views.status'),
    url(r'^info/$', 'api.views.info'),
    url(r'^filemanager-settings/$', 'api.views.filemanager_settings'),
    url(r'^task-run-attempts/(?P<id>[a-zA-Z0-9_\-]+)/worker-settings/$', 'api.views.worker_settings'),
    url(r'^task-run-attempts/(?P<id>[a-zA-Z0-9_\-]+)/task-run-attempt-log-files/$',
        'api.views.create_task_run_attempt_log_file')
)
