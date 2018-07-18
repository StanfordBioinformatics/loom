from django.test import TestCase, TransactionTestCase, override_settings
from rest_framework import serializers

from api.models import Run
from api.serializers import DataObjectSerializer
from api.serializers import TemplateTagSerializer, DataTagSerializer, RunTagSerializer
from api.serializers import TemplateSerializer
from . import fixtures, get_mock_context, create_run_from_template


class TestTemplateTagSerializer(TestCase):

    def testCreate(self):
        template = self.create_template()
        tag = self.create_tag(template)
        self.assertEqual(tag.template.uuid, template.uuid)

    def testRender(self):
        template = self.create_template()
        tag = self.create_tag(template)
        tag_data = TemplateTagSerializer(tag).data
        self.assertEqual(tag_data.get('tag'), 'tag1')

    def create_tag(self, template):
        tag_data = {
            'tag': 'tag1',
        }
        context = {'template': template}

        s = TemplateTagSerializer(data=tag_data, context=context)
        s.is_valid(raise_exception=True)
        return s.save()

    def create_template(self):
        with self.settings(TEST_DISABLE_ASYNC_DELAY=True):
            s = TemplateSerializer(data=fixtures.templates.step_a)
            s.is_valid(raise_exception=True)
            template = s.save()
        return template

@override_settings(TEST_DISABLE_ASYNC_DELAY=True,
                   TEST_NO_PUSH_INPUTS=True)
class TestRunTagSerializer(TransactionTestCase):

    def testCreate(self):
        run = self.create_run()
        tag = self.create_tag(run)
        self.assertEqual(tag.run.uuid, run.uuid)

    def testRender(self):
        run = self.create_run()
        tag = self.create_tag(run)
        context = {'run': run}
        tag_data = RunTagSerializer(tag, context=context).data
        self.assertEqual(tag_data.get('tag'), 'tag1')

    def create_tag(self, run):
        tag_data = {'tag': 'tag1'}
        context = {'run': run}
        s = RunTagSerializer(data=tag_data, context=context)
        s.is_valid(raise_exception=True)
        return s.save()

    def create_run(self):
        with self.settings(TEST_DISABLE_ASYNC_DELAY=True):
            s = TemplateSerializer(data=fixtures.templates.step_a)
            s.is_valid(raise_exception=True)
            template = s.save()
            run = create_run_from_template(template)
        return run


class TestDataTagSerializer(TestCase):

    def testCreate(self):
        file = self.create_file()
        tag = self.create_tag(file)
        self.assertEqual(tag.data_object.uuid, file.uuid)
        
    def create_file(self):
        data = fixtures.data_objects.file_data_object
        s = DataObjectSerializer(data=data)
        s.is_valid(raise_exception=True)
        return s.save()

    def create_tag(self, file):
        tag_data = {'tag': 'tag1'}
        context = {'data_object': file}
        s = DataTagSerializer(data=tag_data, context=context)
        s.is_valid(raise_exception=True)
        return s.save()
