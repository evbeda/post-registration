from django.conf.urls import url

from post_registration.views import HomeView
from .views import EventsView, DocFormView

urlpatterns = [
    url(r'docs_form/$', DocFormView.as_view(template_name='doc_form.html'), name='doc_form'),
    url(r'events/$', EventsView.as_view(), name='events'),
    url(r'^$', HomeView.as_view(), name='index'),
]
