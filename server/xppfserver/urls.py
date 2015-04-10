from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^status$', 'apps.controls.views.status'),
    url(r'^analyses$', 'apps.analysis.views.analyses'),
    url(r'^analyses/.*$', 'apps.analysis.views.update'),
)
