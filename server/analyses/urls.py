from django.conf.urls import patterns, include, url
from analyses.models import *

urlpatterns = patterns('',
    url(r'^status/?$', 'analyses.views.status'),
    )    

model_classes = [
    Request,
    ]

for cls in model_classes:
    urlpatterns.append(url(r'^%s/?$' % cls.get_name(plural=True), 'analyses.views.create_or_index', {'cls': cls}))
    urlpatterns.append(url(r'^%s/(?P<id>[a-zA-Z0-9_]+)$' % cls.get_name(plural=True), 'analyses.views.show_or_update', {'cls': cls}))
