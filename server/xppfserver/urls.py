from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^status$', 'apps.controls.views.status'),
    url(r'^run$', 'apps.controls.views.run'),
    url(r'^analyses$', 'apps.analysis.views.analyses'),
    url(r'^analyses/.*$', 'apps.analysis.views.update'),
    url(r'^editor$', 'editor.views.index'),
)

from django.contrib.staticfiles.urls import staticfiles_urlpatterns
urlpatterns += staticfiles_urlpatterns()
