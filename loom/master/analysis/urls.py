from django.conf.urls import patterns, include, url
from analysis.models import *

urlpatterns = [
    url(r'^api/status/?$', 'analysis.views.status'),
    url(r'^api/submitworkflow/?$', 'analysis.views.submitworkflow'),
    url(r'^api/submitresult/?$', 'analysis.views.submitresult'),
    url(r'^api/closerun/?$', 'analysis.views.closerun'),
    url(r'^api/workerinfo/?$', 'analysis.views.workerinfo'),
    url(r'^api/filehandlerinfo/?$', 'analysis.views.filehandlerinfo'),
    ]

model_classes = [
    File,
    FileArray,
    Workflow,
    FileStorageLocation,
    Step,
    StepDefinition,
    StepRun,
    StepResult,
    ]

for cls in model_classes:
    urlpatterns.append(url(r'^api/%s/?$' % cls.get_name(plural=True), 'analysis.views.create_or_index', {'model_class': cls}))
    urlpatterns.append(url(r'^api/%s/(?P<id>[a-zA-Z0-9_\-]+)$' % cls.get_name(plural=True), 'analysis.views.show_or_update', {'model_class': cls}))

urlpatterns.append(url(r'^api/%s/(?P<id>[a-zA-Z0-9_\-]+)/input_port_bundles/?$' % StepRun.get_name(plural=True), 'analysis.views.show_input_port_bundles'))

urlpatterns.append(url(r'^$', 'analysis.views.dashboard'))
