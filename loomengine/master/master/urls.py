from django.conf import settings
from django.conf.urls import include, url
from django.views.generic.base import RedirectView
from django.conf.urls.static import static

urlpatterns = [
    url(r'^api/', include('api.urls')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^$', RedirectView.as_view(url='/api/', permanent=False), name='api'),
]

# For development only. This works when LOOM_DEBUG = True
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
