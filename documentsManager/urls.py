from django.conf.urls import url
from post_registration.views import HomeView
from .views import EventsView, DocFormView , DocsView

urlpatterns = [
    url(r'doc_form/(?P<event_id>\d+)/$', DocFormView.as_view(), name='doc_form'),
    url(r'docs/(?P<event_id>\d+)/$', DocsView.as_view(template_name='docs.html'), name='docs'),
    url(r'events/$', EventsView.as_view(), name='events'),
    url(r'^$', HomeView.as_view(), name='index'),
]
