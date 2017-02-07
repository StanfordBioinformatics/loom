from django.conf.urls import include, url
from rest_framework import routers

import api.views

router = routers.DefaultRouter()

router.register('abstract-workflows', api.views.AbstractWorkflowViewSet, base_name='Workflow')
router.register('imported-workflows', api.views.ImportedWorkflowViewSet, base_name='ImportedWorkflow')
router.register('files', api.views.FileDataObjectViewSet, base_name='FileDataObject')
router.register('imported-files', api.views.ImportedFileDataObjectViewSet, base_name='ImportedFile')
router.register('result-files', api.views.ResultFileDataObjectViewSet, base_name='ResultFile')
router.register('log-files', api.views.LogFileDataObjectViewSet, base_name='LogFile')
router.register('run-requests', api.views.RunRequestViewSet, base_name='RunRequest')
router.register('abstract-workflow-runs', api.views.AbstractWorkflowRunViewSet)
router.register('task-runs', api.views.TaskRunViewSet)
router.register('task-run-attempts', api.views.TaskRunAttemptViewSet)
router.register('task-run-attempt-outputs', api.views.TaskRunAttemptOutputViewSet)
router.register('file-imports', api.views.FileImportViewSet)
router.register('file-locations', api.views.FileLocationViewSet)

file_provenance_detail = api.views.FileProvenanceViewSet.as_view({'get':'retrieve'})

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^files/(?P<pk>[a-zA-Z0-9]+)/provenance/$', file_provenance_detail, name='file_provenance_detail'),
    url(r'^status/$', api.views.status),
    url(r'^info/$', api.views.info),
    url(r'^filemanager-settings/$', api.views.filemanager_settings),
    url(r'^task-run-attempts/(?P<id>[a-zA-Z0-9_\-]+)/worker-settings/$', api.views.worker_settings),
    url(r'^task-run-attempts/(?P<id>[a-zA-Z0-9_\-]+)/task-run-attempt-log-files/$',
        api.views.create_task_run_attempt_log_file),
    url(r'^task-run-attempts/(?P<id>[a-zA-Z0-9_\-]+)/task-run-attempt-errors/$',
        api.views.create_task_run_attempt_error)
]
