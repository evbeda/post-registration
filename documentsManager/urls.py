from django.conf.urls import url

from post_registration.views import HomeView
from .views import EventsView, DocFormView

urlpatterns = [
    url(r'events/$', EventsView.as_view(template_name='events.html'), name='events'),
    url(r'docs_form/$', DocFormView.as_view(template_name='doc_form.html'), name='doc_form'),
    url(r'^$', HomeView.as_view(template_name='index.html'), name='index'),
]
