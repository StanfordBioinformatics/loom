from django.test import TestCase
from rest_framework import serializers

from api.serializers.tags import TagSerializer
from api.serializers.templates import TemplateSerializer
from . import fixtures
from . import get_mock_context

class TestTagSerializer(TestCase):

    def testCreate(self):
        template = self.create_template()
        tag = self.create_tag(template)
        self.assertEqual(tag.template.uuid, template.uuid)

    def testRender(self):
        template = self.create_template()
        tag = self.create_tag(template)
        context = get_mock_context()
        tag_data = TagSerializer(tag, context=context).data
        self.assertEqual(tag_data.get('type'), 'template')
        self.assertEqual(tag_data.get('name'), 'tag1')
        self.assertEqual(tag_data.get('target').get('uuid'),
                         str(template.uuid))
        
    def create_tag(self, template):
        template_id = '@%s' % template.uuid
        tag_data = {
            'name': 'tag1',
            'target': template_id
        }
        s = TagSerializer(data=tag_data)
        s.is_valid(raise_exception=True)
        return s.save()

    def create_template(self):
        with self.settings(TEST_DISABLE_ASYNC_DELAY=True):
            s = TemplateSerializer(data=fixtures.templates.step_a)
            s.is_valid(raise_exception=True)
            template = s.save()
        return template
