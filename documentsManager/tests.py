from django.core.urlresolvers import resolve
from django.test import TestCase


class DocFormTest(TestCase):
    def test_doc_from_exist(self):
        view = resolve('/docs_form/')
        self.assertEqual(view.view_name, 'doc_form')

    def test_home_url_resolves_home_view(self):
        view = resolve('/')
        self.assertEqual(view.view_name, 'index')
