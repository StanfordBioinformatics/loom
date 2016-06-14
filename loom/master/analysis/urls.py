from django.conf.urls import patterns, include, url
from analysis.models import *

urlpatterns = patterns(
    '',
    url(r'^status/$', 'analysis.views.status'),
    url(r'^info/$', 'analysis.views.info'),
    url(r'^filehandler-settings/$', 'analysis.views.filehandler_settings'),
    url(r'^controls/refresh/$', 'analysis.views.refresh'),
)

model_classes = [
    DataObject,
    AbstractFileImport,
    FileDataObject,
    FileLocation,
    AbstractWorkflow,
    RunRequest,
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
                       'analysis.views.task_run_attempt_log_file'))
