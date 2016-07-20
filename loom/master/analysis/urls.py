from django.conf.urls import patterns, include, url
from rest_framework import routers

from analysis.models import *
from analysis import views

router = routers.DefaultRouter()

router.register(r'abstract-file-imports', views.AbstractFileImportViewSet)
router.register(r'abstract-workflows', views.AbstractWorkflowViewSet)
router.register(r'boolean-contents', views.BooleanContentViewSet)
router.register(r'boolean-data-objects', views.BooleanDataObjectViewSet)
router.register(r'channel-outputs', views.ChannelOutputViewSet)
router.register(r'channels', views.ChannelViewSet)
router.register(r'data-object-contents', views.DataObjectContentViewSet)
router.register(r'data-objects', views.DataObjectViewSet)
router.register(r'file-contents', views.FileContentViewSet)
router.register(r'file-data-objects', views.FileDataObjectViewSet)
router.register(r'file-imports', views.FileImportViewSet)
router.register(r'file-locations', views.FileLocationViewSet)
router.register(r'fixed-step-inputs', views.FixedStepInputViewSet)
router.register(r'fixed-workflow-inputs', views.FixedWorkflowInputViewSet)
router.register(r'google-cloud-task-run-attempts', views.GoogleCloudTaskRunAttemptViewSet)
router.register(r'input-output-nodes', views.InputOutputNodeViewSet)
router.register(r'integer-contents', views.IntegerContentViewSet)
router.register(r'integer-data-objects', views.IntegerDataObjectViewSet)
router.register(r'local-task-run-attempts', views.LocalTaskRunAttemptViewSet)
router.register(r'mock-task-run-attempts', views.MockTaskRunAttemptViewSet)
router.register(r'requested-docker-environments', views.RequestedDockerEnvironmentViewSet)
router.register(r'requested-environments', views.RequestedEnvironmentViewSet)
router.register(r'requested-resource-sets', views.RequestedResourceSetViewSet)
router.register(r'step-inputs', views.StepInputViewSet)
router.register(r'step-outputs', views.StepOutputViewSet)
router.register(r'steps', views.StepViewSet)
router.register(r'string-contents', views.StringContentViewSet)
router.register(r'string-data-objects', views.StringDataObjectViewSet)
router.register(r'task-definition-inputs', views.TaskDefinitionInputViewSet)
router.register(r'task-definition-outputs', views.TaskDefinitionOutputViewSet)
router.register(r'task-definition-docker-environment', views.TaskDefinitionDockerEnvironmentViewSet)
router.register(r'task-definition-environment', views.TaskDefinitionEnvironmentViewSet)
router.register(r'task-definitions', views.TaskDefinitionViewSet)
router.register(r'task-run-attempt-output-file-imports', views.TaskRunAttemptOutputFileImportViewSet)
router.register(r'task-run-attempt-outputs', views.TaskRunAttemptOutputViewSet)
router.register(r'task-run-attempt-log-file-imports', views.TaskRunAttemptLogFileImportViewSet)
router.register(r'task-run-attempt-log-files', views.TaskRunAttemptLogFileViewSet)
router.register(r'task-run-attempts', views.TaskRunAttemptViewSet)
router.register(r'task-run-inputs', views.TaskRunInputViewSet)
router.register(r'task-run-outputs', views.TaskRunOutputViewSet)
router.register(r'task-runs', views.TaskRunViewSet)
router.register(r'unnamed-file-contents', views.UnnamedFileContentViewSet)
router.register(r'workflow-inputs', views.WorkflowInputViewSet)
router.register(r'workflow-outputs', views.WorkflowOutputViewSet)
router.register(r'workflows', views.WorkflowViewSet)

router.register(r'abstract-workflow-runs', views.AbstractWorkflowRunViewSet)
router.register(r'workflow-runs', views.WorkflowRunViewSet)
router.register(r'step-runs', views.StepRunViewSet)
router.register(r'abstract-step-run-inputs', views.AbstractStepRunInputViewSet)
router.register(r'step-run-inputs', views.StepRunInputViewSet)
router.register(r'fixed-step-run-inputs', views.FixedStepRunInputViewSet)
router.register(r'step-run-outputs', views.StepRunOutputViewSet)
router.register(r'workflow-run-inputs', views.WorkflowRunInputViewSet)
router.register(r'fixed-workflow-run-inputs', views.FixedWorkflowRunInputViewSet)
router.register(r'workflow-run-outputs', views.WorkflowRunOutputViewSet)

router.register(r'run-requests', views.RunRequestViewSet)
router.register(r'run-request-inputs', views.RunRequestInputViewSet)
router.register(r'run-request-outputs', views.RunRequestOutputViewSet)
router.register(r'cancel-requests', views.CancelRequestViewSet)
router.register(r'restart-requests', views.RestartRequestViewSet)
router.register(r'failure-notices', views.FailureNoticeViewSet)



urlpatterns = patterns(
    '',
    url(r'^', include(router.urls)),
    #url(r'^status/$', 'analysis.views.status'),
    #url(r'^info/$', 'analysis.views.info'),
    #url(r'^filehandler-settings/$', 'analysis.views.filehandler_settings'),
    #url(r'^controls/refresh/$', 'analysis.views.refresh'),
)

"""
urlpatterns.append(url(r'^%s/(?P<id>[a-zA-Z0-9_\-]+)/file-locations/$' % FileDataObject.get_class_name(plural=True, hyphen=True), 'analysis.views.locations_by_file'))
urlpatterns.append(url(r'^%s/(?P<id>[a-zA-Z0-9_\-]+)/file-imports/$' % FileDataObject.get_class_name(plural=True, hyphen=True), 'analysis.views.file_imports_by_file'))
urlpatterns.append(url(r'^%s/(?P<id>[a-zA-Z0-9_\-]+)/source-runs/$' % FileDataObject.get_class_name(plural=True, hyphen=True), 'analysis.views.file_data_source_runs'))
urlpatterns.append(url(r'^%s/(?P<id>[a-zA-Z0-9_\-]+)/worker-settings/$' % TaskRunAttempt.get_class_name(plural=True, hyphen=True), 'analysis.views.worker_settings'))
urlpatterns.append(url(r'^%s/(?P<id>[a-zA-Z0-9_\-]+)/%s/$' %
                       (TaskRunAttempt.get_class_name(plural=True, hyphen=True),
                        TaskRunAttemptLogFile.get_class_name(plural=True, hyphen=True)),
                       'analysis.views.create_task_run_attempt_log_file'))
urlpatterns.append(url(r'^imported-file-data-objects/$', 'analysis.views.imported_file_data_objects'))
urlpatterns.append(url(r'^result-file-data-objects/$', 'analysis.views.result_file_data_objects'))
"""
