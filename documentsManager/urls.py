from django.conf.urls import url

from .views import (
    EventsView,
    DocFormView,
    DocsView,
    HomeView,
    FileDocUpdate,
    TextDocUpdate,
    select_event,
)

urlpatterns = [
    url(r'doc_form/(?P<event_id>\d+)/$', DocFormView.as_view(), name='doc_form'),
    url(r'^docs/file/edit/(?P<id>\d+)/$',
        FileDocUpdate.as_view(), name="edit-filedoc"),
    url(r'^docs/text/edit/(?P<id>\d+)/$',
        TextDocUpdate.as_view(), name="edit-textdoc"),
    url(r'docs/(?P<event_id>\d+)/$', DocsView.as_view(), name='docs'),
    url(r'events/$', EventsView.as_view(), name='events'),
    url(r'events/(?P<eb_event_id>\d+)/$', select_event, name='events'),
    url(r'^$', HomeView.as_view(), name='home'),
]
