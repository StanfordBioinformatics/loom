from django.conf.urls import patterns, include, url
from analysis.models import *

urlpatterns = patterns(
    '',
    url(r'^status/?$', 'analysis.views.status'),
    url(r'^submitrequest/?$', 'analysis.views.submitrequest'),
    url(r'^submitresult/?$', 'analysis.views.submitresult'),
    url(r'^closerun/?$', 'analysis.views.closerun'),
    )    

model_classes = [
    File,
    Workflow,
    FileLocation,
    RequestSubmission,
    StepRequest,
    StepRun,
    StepResult,
    ]

for cls in model_classes:
    urlpatterns.append(url(r'^%s/?$' % cls.get_name(plural=True), 'analysis.views.create_or_index', {'cls': cls}))
    urlpatterns.append(url(r'^%s/(?P<id>[a-zA-Z0-9_\-]+)$' % cls.get_name(plural=True), 'analysis.views.show_or_update', {'cls': cls}))

urlpatterns.append(url(r'^%s/(?P<id>[a-zA-Z0-9_\-]+)/input_port_bundles/?$' % StepRun.get_name(plural=True), 'analysis.views.show_input_port_bundles'))
