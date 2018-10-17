from django.conf.urls import url

from .views import (
    EventsView,
    DocFormView,
    DocsView,
    HomeView,
    FileDocUpdate,
    TextDocUpdate,
    FileDocDelete,
    TextDocDelete,
    select_event,
    Landing,
)

urlpatterns = [
    url(r'landing/(?P<event_id>\d+)/$', Landing.as_view(), name='landing'),
    url(r'doc_form/(?P<event_id>\d+)/$', DocFormView.as_view(), name='doc_form'),
    url(r'^event/(?P<event_id>\d+)/docs/file/(?P<pk>\d+)/edit/$',
        FileDocUpdate.as_view(), name="edit-filedoc"),
    url(r'^event/(?P<event_id>\d+)/docs/text/(?P<pk>\d+)/edit/$',
        TextDocUpdate.as_view(), name="edit-textdoc"),
    url(r'^event/(?P<event_id>\d+)/docs/file/(?P<pk>\d+)/delete/$',
        FileDocDelete.as_view(), name="delete-filedoc"),
    url(r'^event/(?P<event_id>\d+)/docs/text/(?P<pk>\d+)/delete/$',
        TextDocDelete.as_view(), name="delete-textdoc"),
    url(r'docs/(?P<event_id>\d+)/$', DocsView.as_view(), name='docs'),
    url(r'events/$', EventsView.as_view(), name='events'),
    url(r'events/(?P<eb_event_id>\d+)/$', select_event, name='events'),
    url(r'^$', HomeView.as_view(), name='home'),
]
