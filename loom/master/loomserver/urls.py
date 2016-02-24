from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^api/', include('analysis.urls')),
    url(r'^editor$', 'editor.views.index'),
    url(r'^$', 'analysis.views.browser'),
)

from django.contrib.staticfiles.urls import staticfiles_urlpatterns
urlpatterns += staticfiles_urlpatterns()
