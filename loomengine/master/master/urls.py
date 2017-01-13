from django.conf.urls import include, url
from django.views.generic.base import RedirectView

urlpatterns = [
    url(r'^api/', include('api.urls')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^$', RedirectView.as_view(url='/api/', permanent=False), name='api'),
]
