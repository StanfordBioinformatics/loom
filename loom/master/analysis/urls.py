from django.conf.urls import patterns, include, url
from analysis.models import *

urlpatterns = patterns(
    '',
    url(r'^status/$', 'analysis.views.status'),
    url(r'^info/$', 'analysis.views.info'),
    url(r'^worker-info/$', 'analysis.views.worker_info'),
    url(r'^file-handler-info/$', 'analysis.views.file_handler_info'),
    url(r'^server-time/$', 'analysis.views.server_time'),
    url(r'^controls/check-status/$', 'analysis.views.check_status'),
)

model_classes = [
    DataObject,
    FileImport,
    FileDataObject,
    FileLocation,
    AbstractWorkflow,
    WorkflowRun,
    RunRequest,
    Step,
    StepRun,
    TaskRun,
    TaskRunLog,
]

for cls in model_classes:
    urlpatterns.append(url(r'^%s/$' % cls.get_class_name(plural=True, hyphen=True), 'analysis.views.create_or_index', {'model_class': cls}))
    urlpatterns.append(url(r'^%s/(?P<id>[a-zA-Z0-9_\-]+)/$' % cls.get_class_name(plural=True, hyphen=True), 'analysis.views.show_or_update', {'model_class': cls}))

urlpatterns.append(url(r'^%s/(?P<id>[a-zA-Z0-9_\-]+)/file-locations/$' % FileDataObject.get_class_name(plural=True, hyphen=True), 'analysis.views.locations_by_file'))
urlpatterns.append(url(r'^%s/(?P<id>[a-zA-Z0-9_\-]+)/file-imports/$' % FileDataObject.get_class_name(plural=True, hyphen=True), 'analysis.views.file_imports_by_file'))
urlpatterns.append(url(r'^%s/(?P<id>[a-zA-Z0-9_\-]+)/source-runs/$' % FileDataObject.get_class_name(plural=True, hyphen=True), 'analysis.views.file_data_source_runs'))
