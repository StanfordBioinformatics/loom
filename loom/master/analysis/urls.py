from django.conf.urls import patterns, include, url
from rest_framework import routers

from analysis.models import *
from analysis import views

router = routers.DefaultRouter()
router.register(r'unnamed-file-contents', views.UnnamedFileContentViewSet)
router.register(r'file-contents', views.FileContentViewSet)
router.register(r'file-locations', views.FileLocationViewSet)
router.register(r'abstract-file-imports', views.AbstractFileImportViewSet)
router.register(r'file-imports', views.FileImportViewSet)
router.register(r'file-data-objects', views.FileDataObjectViewSet)

urlpatterns = patterns(
    '',
    url(r'^', include(router.urls)),
    #url(r'^status/$', 'analysis.views.status'),
    #url(r'^info/$', 'analysis.views.info'),
    #url(r'^filehandler-settings/$', 'analysis.views.filehandler_settings'),
    #url(r'^controls/refresh/$', 'analysis.views.refresh'),
)

"""
model_classes = [
    DataObject,
    AbstractFileImport,
    FileDataObject,
    FileLocation,
    AbstractWorkflow,
    RunRequest,
    AbstractWorkflowRun,
    WorkflowRun,
    StepRun,
    TaskRun,
    TaskRunAttempt,
    TaskRunAttemptOutput,
]

for cls in model_classes:
    urlpatterns.append(url(r'^%s/$' % cls.get_class_name(plural=True, hyphen=True), 'analysis.views.create_or_index', {'model_class': cls}))
    urlpatterns.append(url(r'^%s/(?P<id>[a-zA-Z0-9_\-]+)/$' % cls.get_class_name(plural=True, hyphen=True), 'analysis.views.show_or_update', {'model_class': cls}))

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
