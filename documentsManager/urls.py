from django.conf.urls import url, include
from ../post_registration/views import HomeView
from .views import EventsView


urlpatterns = [
    url(r'^$', HomeView.as_view(template_name='index.html'), name='index'),
    url(r'events/', EventsView.as_view(template_name='events.html', name='events'))
]
