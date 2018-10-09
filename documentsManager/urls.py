from django.conf.urls import url

from .views import (
    EventsView,
    DocFormView,
    DocsView,
    HomeView,
    select_event,
    update_dates,
)

urlpatterns = [
    url(r'doc_form/(?P<event_id>\d+)/$', DocFormView.as_view(), name='doc_form'),
    url(r'docs/(?P<event_id>\d+)/$', DocsView.as_view(), name='docs'),
    url(r'events/$', EventsView.as_view(), name='events'),
    url(r'events/(?P<eb_event_id>\d+)/$', select_event, name='events'),
    url(r'events/(?P<event_id>\d+)/dates/$', update_dates, name='update_dates'),
    url(r'^$', HomeView.as_view(), name='home'),
]
