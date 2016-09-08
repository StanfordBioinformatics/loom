from django.conf.urls import patterns, include, url
from rest_framework import routers

from api.models import *
from api import views


router = routers.DefaultRouter()

router.register(AbstractWorkflowRun.get_class_name(plural=True, hyphen=True), views.AbstractWorkflowRunViewSet)
router.register(BooleanContent.get_class_name(plural=True, hyphen=True), views.BooleanContentViewSet)
router.register(BooleanDataObject.get_class_name(plural=True, hyphen=True), views.BooleanDataObjectViewSet)
#router.register(CancelRequest.get_class_name(plural=True, hyphen=True), views.CancelRequestViewSet)
router.register(DataObject.get_class_name(plural=True, hyphen=True), views.DataObjectViewSet, base_name='DataObject')
router.register(DataObjectContent.get_class_name(plural=True, hyphen=True), views.DataObjectContentViewSet)
#router.register(FailureNotice.get_class_name(plural=True, hyphen=True), views.FailureNoticeViewSet)
router.register(FileContent.get_class_name(plural=True, hyphen=True), views.FileContentViewSet)
router.register(FileDataObject.get_class_name(plural=True, hyphen=True), views.FileDataObjectViewSet, base_name='FileDataObject')
router.register('imported-file-data-objects', views.ImportedFileDataObjectViewSet)
router.register('result-file-data-objects', views.ResultFileDataObjectViewSet)
router.register('log-file-data-objects', views.LogFileDataObjectViewSet)
router.register(FileImport.get_class_name(plural=True, hyphen=True), views.FileImportViewSet)
router.register(FileLocation.get_class_name(plural=True, hyphen=True), views.FileLocationViewSet)
router.register(IntegerContent.get_class_name(plural=True, hyphen=True), views.IntegerContentViewSet)
router.register(IntegerDataObject.get_class_name(plural=True, hyphen=True), views.IntegerDataObjectViewSet)
#router.register(RestartRequest.get_class_name(plural=True, hyphen=True), views.RestartRequestViewSet)
router.register(RunRequest.get_class_name(plural=True, hyphen=True), views.RunRequestViewSet)
#router.register(Step.get_class_name(plural=True, hyphen=True), views.StepViewSet)
#router.register(StepRun.get_class_name(plural=True, hyphen=True), views.StepRunViewSet)
router.register(StringContent.get_class_name(plural=True, hyphen=True), views.StringContentViewSet)
router.register(StringDataObject.get_class_name(plural=True, hyphen=True), views.StringDataObjectViewSet)
#router.register(TaskDefinition.get_class_name(plural=True, hyphen=True), views.TaskDefinitionViewSet)
router.register(TaskRun.get_class_name(plural=True, hyphen=True), views.TaskRunViewSet)
router.register(TaskRunAttempt.get_class_name(plural=True, hyphen=True), views.TaskRunAttemptViewSet)
#router.register(TaskRunAttemptLogFile.get_class_name(plural=True, hyphen=True), views.TaskRunAttemptLogFileImportViewSet)
#router.register(TaskRunAttemptLogFile.get_class_name(plural=True, hyphen=True), views.TaskRunAttemptLogFileViewSet)
router.register(TaskRunAttemptOutput.get_class_name(plural=True, hyphen=True), views.TaskRunAttemptOutputViewSet)
#router.register(TaskRunAttemptOutputFileImport.get_class_name(plural=True, hyphen=True), views.TaskRunAttemptOutputFileImportViewSet)
router.register(UnnamedFileContent.get_class_name(plural=True, hyphen=True), views.UnnamedFileContentViewSet)
router.register(AbstractWorkflow.get_class_name(plural=True, hyphen=True), views.AbstractWorkflowViewSet, base_name='AbstractWorkflow')
router.register('imported-workflows', views.ImportedWorkflowViewSet)
#router.register(Workflow.get_class_name(plural=True, hyphen=True), views.WorkflowViewSet)
#router.register(WorkflowRun.get_class_name(plural=True, hyphen=True), views.WorkflowRunViewSet)

file_provenance_detail = views.FileProvenanceViewSet.as_view({'get':'retrieve'})

urlpatterns = patterns(
    '',
    url(r'^', include(router.urls)),
    url(r'^file-data-objects/(?P<pk>[a-zA-Z0-9]+)/provenance/$', file_provenance_detail, name='file_provenance_detail'),
    url(r'^status/$', 'api.views.status'),
    url(r'^info/$', 'api.views.info'),
    url(r'^filehandler-settings/$', 'api.views.filehandler_settings'),
    url(r'^%s/(?P<id>[a-zA-Z0-9_\-]+)/worker-settings/$' % TaskRunAttempt.get_class_name(plural=True, hyphen=True), 'api.views.worker_settings'),
    #url(r'^controls/refresh/$', 'api.views.refresh'),
    url(r'^%s/(?P<id>[a-zA-Z0-9_\-]+)/%s/$' %
        (TaskRunAttempt.get_class_name(plural=True, hyphen=True),
         TaskRunAttemptLogFile.get_class_name(plural=True, hyphen=True)),
        'api.views.create_task_run_attempt_log_file')
)

"""
urlpatterns.append(url(r'^%s/(?P<id>[a-zA-Z0-9_\-]+)/file-locations/$' % FileDataObject.get_class_name(plural=True, hyphen=True), 'api.views.locations_by_file'))
urlpatterns.append(url(r'^%s/(?P<id>[a-zA-Z0-9_\-]+)/file-imports/$' % FileDataObject.get_class_name(plural=True, hyphen=True), 'api.views.file_imports_by_file'))
urlpatterns.append(url(r'^%s/(?P<id>[a-zA-Z0-9_\-]+)/source-runs/$' % FileDataObject.get_class_name(plural=True, hyphen=True), 'api.views.file_data_source_runs'))
urlpatterns.append(url(r'^imported-file-data-objects/$', 'api.views.imported_file_data_objects'))
urlpatterns.append(url(r'^result-file-data-objects/$', 'api.views.result_file_data_objects'))
"""
