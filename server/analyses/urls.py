from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^status$', 'analyses.views.status.status'),
    url(r'^analysis_request$', 'analyses.views.analysis_request.create'),
)
