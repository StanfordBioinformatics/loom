from django.conf.urls import patterns, include, url
from analysis.models import *

urlpatterns = patterns('',
    url(r'^status/?$', 'analysis.views.status'),
    url(r'^submitrequest/?$', 'analysis.views.submitrequest'),
    )    

model_classes = [
    Request,
    ]

for cls in model_classes:
    urlpatterns.append(url(r'^%s/?$' % cls.get_name(plural=True), 'analysis.views.create_or_index', {'cls': cls}))
    urlpatterns.append(url(r'^%s/(?P<id>[a-zA-Z0-9_]+)$' % cls.get_name(plural=True), 'analysis.views.show_or_update', {'cls': cls}))
