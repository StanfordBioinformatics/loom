from django.conf import settings
from django.conf.urls import include, url
from django.views.generic.base import RedirectView
from django.conf.urls.static import static


urlpatterns = [
    url(r'^api/', include('api.urls')),
    url(r'^$', RedirectView.as_view(url='/api/', permanent=False), name='api'),
]
if settings.LOGIN_REQUIRED:
    urlpatterns.append(
        url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')))

# For development only. This works when LOOM_DEBUG = True
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns.append(url(r'^portal/$', RedirectView.as_view(url='/portal/index.html', permanent=False), name='api'))
    urlpatterns += static(r'portal/', document_root=settings.PORTAL_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
