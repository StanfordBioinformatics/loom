from django.conf.urls import patterns, include, url
from rest_framework import routers

from analysis.models import *
from analysis import views


router = routers.DefaultRouter()

#router.register(AbstractStepRunInput.get_class_name(plural=True, hyphen=True), views.AbstractStepRunInputViewSet)
#router.register(AbstractWorkflow.get_class_name(plural=True, hyphen=True), views.AbstractWorkflowViewSet)
#router.register(AbstractWorkflowRun.get_class_name(plural=True, hyphen=True), views.AbstractWorkflowRunViewSet)
router.register(BooleanContent.get_class_name(plural=True, hyphen=True), views.BooleanContentViewSet)
router.register(BooleanDataObject.get_class_name(plural=True, hyphen=True), views.BooleanDataObjectViewSet)
#router.register(CancelRequest.get_class_name(plural=True, hyphen=True), views.CancelRequestViewSet)
#router.register(Channel.get_class_name(plural=True, hyphen=True), views.ChannelViewSet)
#router.register(ChannelOutput.get_class_name(plural=True, hyphen=True), views.ChannelOutputViewSet)
router.register(DataObject.get_class_name(plural=True, hyphen=True), views.DataObjectViewSet, base_name='DataObject')
router.register(DataObjectContent.get_class_name(plural=True, hyphen=True), views.DataObjectContentViewSet)
#router.register(FailureNotice.get_class_name(plural=True, hyphen=True), views.FailureNoticeViewSet)
router.register(FileContent.get_class_name(plural=True, hyphen=True), views.FileContentViewSet)
router.register(FileDataObject.get_class_name(plural=True, hyphen=True), views.FileDataObjectViewSet)
router.register(FileImport.get_class_name(plural=True, hyphen=True), views.FileImportViewSet)
router.register(FileLocation.get_class_name(plural=True, hyphen=True), views.FileLocationViewSet)
#router.register(FixedStepInput.get_class_name(plural=True, hyphen=True), views.FixedStepInputViewSet)
#router.register(FixedStepRunInput.get_class_name(plural=True, hyphen=True), views.FixedStepRunInputViewSet)
#router.register(FixedWorkflowInput.get_class_name(plural=True, hyphen=True), views.FixedWorkflowInputViewSet)
#router.register(FixedWorkflowRunInput.get_class_name(plural=True, hyphen=True), views.FixedWorkflowRunInputViewSet)
#router.register(GoogleCloudTaskRunAttempt.get_class_name(plural=True, hyphen=True), views.GoogleCloudTaskRunAttemptViewSet)
#router.register(InputOutputNode.get_class_name(plural=True, hyphen=True), views.InputOutputNodeViewSet)
router.register(IntegerContent.get_class_name(plural=True, hyphen=True), views.IntegerContentViewSet)
router.register(IntegerDataObject.get_class_name(plural=True, hyphen=True), views.IntegerDataObjectViewSet)
#router.register(LocalTaskRunAttempt.get_class_name(plural=True, hyphen=True), views.LocalTaskRunAttemptViewSet)
#router.register(MockTaskRunAttempt.get_class_name(plural=True, hyphen=True), views.MockTaskRunAttemptViewSet)
#router.register(RequestedDockerEnvironment.get_class_name(plural=True, hyphen=True), views.RequestedDockerEnvironmentViewSet)
#router.register(RequestedEnvironment.get_class_name(plural=True, hyphen=True), views.RequestedEnvironmentViewSet)
#router.register(RequestedResourceSet.get_class_name(plural=True, hyphen=True), views.RequestedResourceSetViewSet)
#router.register(RestartRequest.get_class_name(plural=True, hyphen=True), views.RestartRequestViewSet)
#router.register(RunRequest.get_class_name(plural=True, hyphen=True), views.RunRequestViewSet)
#router.register(RunRequestInput.get_class_name(plural=True, hyphen=True), views.RunRequestInputViewSet)
#router.register(RunRequestOutput.get_class_name(plural=True, hyphen=True), views.RunRequestOutputViewSet)
#router.register(Step.get_class_name(plural=True, hyphen=True), views.StepViewSet)
#router.register(StepInput.get_class_name(plural=True, hyphen=True), views.StepInputViewSet)
#router.register(StepOutput.get_class_name(plural=True, hyphen=True), views.StepOutputViewSet)
#router.register(StepRun.get_class_name(plural=True, hyphen=True), views.StepRunViewSet)
#router.register(StepRunInput.get_class_name(plural=True, hyphen=True), views.StepRunInputViewSet)
#router.register(StepRunOutput.get_class_name(plural=True, hyphen=True), views.StepRunOutputViewSet)
router.register(StringContent.get_class_name(plural=True, hyphen=True), views.StringContentViewSet)
router.register(StringDataObject.get_class_name(plural=True, hyphen=True), views.StringDataObjectViewSet)
#router.register(TaskDefinition.get_class_name(plural=True, hyphen=True), views.TaskDefinitionViewSet)
#router.register(TaskDefinitionDockerEnvironment.get_class_name(plural=True, hyphen=True), views.TaskDefinitionDockerEnvironmentViewSet)
#router.register(TaskDefinitionEnvironment.get_class_name(plural=True, hyphen=True), views.TaskDefinitionEnvironmentViewSet)
#router.register(TaskDefinitionInput.get_class_name(plural=True, hyphen=True), views.TaskDefinitionInputViewSet)
#router.register(TaskDefinitionOutput.get_class_name(plural=True, hyphen=True), views.TaskDefinitionOutputViewSet)
#router.register(TaskRun.get_class_name(plural=True, hyphen=True), views.TaskRunViewSet)
#router.register(TaskRunAttempt.get_class_name(plural=True, hyphen=True), views.TaskRunAttemptViewSet)
#router.register(TaskRunAttemptLogFile.get_class_name(plural=True, hyphen=True), views.TaskRunAttemptLogFileImportViewSet)
#router.register(TaskRunAttemptLogFile.get_class_name(plural=True, hyphen=True), views.TaskRunAttemptLogFileViewSet)
#router.register(TaskRunAttemptOutput.get_class_name(plural=True, hyphen=True), views.TaskRunAttemptOutputViewSet)
#router.register(TaskRunAttemptOutputFileImport.get_class_name(plural=True, hyphen=True), views.TaskRunAttemptOutputFileImportViewSet)
#router.register(TaskRunInput.get_class_name(plural=True, hyphen=True), views.TaskRunInputViewSet)
#router.register(TaskRunOutput.get_class_name(plural=True, hyphen=True), views.TaskRunOutputViewSet)
router.register(UnnamedFileContent.get_class_name(plural=True, hyphen=True), views.UnnamedFileContentViewSet)
#router.register(Workflow.get_class_name(plural=True, hyphen=True), views.WorkflowViewSet)
#router.register(WorkflowInput.get_class_name(plural=True, hyphen=True), views.WorkflowInputViewSet)
#router.register(WorkflowOutput.get_class_name(plural=True, hyphen=True), views.WorkflowOutputViewSet)
#router.register(WorkflowRun.get_class_name(plural=True, hyphen=True), views.WorkflowRunViewSet)
#router.register(WorkflowRunInput.get_class_name(plural=True, hyphen=True), views.WorkflowRunInputViewSet)
#router.register(WorkflowRunOutput.get_class_name(plural=True, hyphen=True), views.WorkflowRunOutputViewSet)

urlpatterns = patterns(
    '',
    url(r'^', include(router.urls)),
    url(r'^status/$', 'analysis.views.status'),
    url(r'^info/$', 'analysis.views.info'),
    url(r'^filehandler-settings/$', 'analysis.views.filehandler_settings'),
#    url(r'^%s/(?P<id>[a-zA-Z0-9_\-]+)/worker-settings/$' % TaskRunAttempt.get_class_name(plural=True, hyphen=True), 'analysis.views.worker_settings'),
    #url(r'^controls/refresh/$', 'analysis.views.refresh'),
)

"""
urlpatterns.append(url(r'^%s/(?P<id>[a-zA-Z0-9_\-]+)/file-locations/$' % FileDataObject.get_class_name(plural=True, hyphen=True), 'analysis.views.locations_by_file'))
urlpatterns.append(url(r'^%s/(?P<id>[a-zA-Z0-9_\-]+)/file-imports/$' % FileDataObject.get_class_name(plural=True, hyphen=True), 'analysis.views.file_imports_by_file'))
urlpatterns.append(url(r'^%s/(?P<id>[a-zA-Z0-9_\-]+)/source-runs/$' % FileDataObject.get_class_name(plural=True, hyphen=True), 'analysis.views.file_data_source_runs'))
urlpatterns.append(url(r'^%s/(?P<id>[a-zA-Z0-9_\-]+)/%s/$' %
                       (TaskRunAttempt.get_class_name(plural=True, hyphen=True),
                        TaskRunAttemptLogFile.get_class_name(plural=True, hyphen=True)),
                       'analysis.views.create_task_run_attempt_log_file'))
urlpatterns.append(url(r'^imported-file-data-objects/$', 'analysis.views.imported_file_data_objects'))
urlpatterns.append(url(r'^result-file-data-objects/$', 'analysis.views.result_file_data_objects'))
"""
