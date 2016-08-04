from django.conf.urls import patterns, include, url
from rest_framework import routers

from analysis.models import *
from analysis import views


router = routers.DefaultRouter()

#router.register(AbstractWorkflowRun.get_class_name(plural=True, hyphen=True), views.AbstractWorkflowRunViewSet)
router.register(BooleanContent.get_class_name(plural=True, hyphen=True), views.BooleanContentViewSet)
router.register(BooleanDataObject.get_class_name(plural=True, hyphen=True), views.BooleanDataObjectViewSet)
#router.register(CancelRequest.get_class_name(plural=True, hyphen=True), views.CancelRequestViewSet)
router.register(DataObject.get_class_name(plural=True, hyphen=True), views.DataObjectViewSet, base_name='DataObject')
router.register(DataObjectContent.get_class_name(plural=True, hyphen=True), views.DataObjectContentViewSet)
#router.register(FailureNotice.get_class_name(plural=True, hyphen=True), views.FailureNoticeViewSet)
router.register(FileContent.get_class_name(plural=True, hyphen=True), views.FileContentViewSet)
router.register(FileDataObject.get_class_name(plural=True, hyphen=True), views.FileDataObjectViewSet)
router.register(FileImport.get_class_name(plural=True, hyphen=True), views.FileImportViewSet)
router.register(FileLocation.get_class_name(plural=True, hyphen=True), views.FileLocationViewSet)
#router.register(GoogleCloudTaskRunAttempt.get_class_name(plural=True, hyphen=True), views.GoogleCloudTaskRunAttemptViewSet)
router.register(IntegerContent.get_class_name(plural=True, hyphen=True), views.IntegerContentViewSet)
router.register(IntegerDataObject.get_class_name(plural=True, hyphen=True), views.IntegerDataObjectViewSet)
#router.register(LocalTaskRunAttempt.get_class_name(plural=True, hyphen=True), views.LocalTaskRunAttemptViewSet)
#router.register(MockTaskRunAttempt.get_class_name(plural=True, hyphen=True), views.MockTaskRunAttemptViewSet)
#router.register(RestartRequest.get_class_name(plural=True, hyphen=True), views.RestartRequestViewSet)
#router.register(RunRequest.get_class_name(plural=True, hyphen=True), views.RunRequestViewSet)
#router.register(Step.get_class_name(plural=True, hyphen=True), views.StepViewSet)
#router.register(StepRun.get_class_name(plural=True, hyphen=True), views.StepRunViewSet)
router.register(StringContent.get_class_name(plural=True, hyphen=True), views.StringContentViewSet)
router.register(StringDataObject.get_class_name(plural=True, hyphen=True), views.StringDataObjectViewSet)
#router.register(TaskDefinition.get_class_name(plural=True, hyphen=True), views.TaskDefinitionViewSet)
#router.register(TaskRun.get_class_name(plural=True, hyphen=True), views.TaskRunViewSet)
#router.register(TaskRunAttempt.get_class_name(plural=True, hyphen=True), views.TaskRunAttemptViewSet)
#router.register(TaskRunAttemptLogFile.get_class_name(plural=True, hyphen=True), views.TaskRunAttemptLogFileImportViewSet)
#router.register(TaskRunAttemptLogFile.get_class_name(plural=True, hyphen=True), views.TaskRunAttemptLogFileViewSet)
#router.register(TaskRunAttemptOutput.get_class_name(plural=True, hyphen=True), views.TaskRunAttemptOutputViewSet)
#router.register(TaskRunAttemptOutputFileImport.get_class_name(plural=True, hyphen=True), views.TaskRunAttemptOutputFileImportViewSet)
router.register(UnnamedFileContent.get_class_name(plural=True, hyphen=True), views.UnnamedFileContentViewSet)
router.register(AbstractWorkflow.get_class_name(plural=True, hyphen=True), views.AbstractWorkflowViewSet, base_name='AbstractWorkflow')
#router.register(Workflow.get_class_name(plural=True, hyphen=True), views.WorkflowViewSet)
#router.register(WorkflowRun.get_class_name(plural=True, hyphen=True), views.WorkflowRunViewSet)

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
