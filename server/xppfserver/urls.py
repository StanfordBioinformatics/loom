from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^status', 'apps.controls.views.status'),
    url(r'^json', 'apps.controls.views.interface'),
    url(r'^run', 'apps.controls.views.run'),
)
