from django.test import TestCase, TransactionTestCase, override_settings
from rest_framework import serializers

from api.models import Run
from api.serializers import DataObjectSerializer
from api.serializers import TemplateLabelSerializer, DataLabelSerializer, RunLabelSerializer
from api.serializers import TemplateSerializer
from . import fixtures, get_mock_context, create_run_from_template


class TestTemplateLabelSerializer(TestCase):

    def testCreate(self):
        template = self.create_template()
        label = self.create_label(template)
        self.assertEqual(label.template.uuid, template.uuid)

    def testRender(self):
        template = self.create_template()
        label = self.create_label(template)
        label_data = TemplateLabelSerializer(label).data
        self.assertEqual(label_data.get('label'), 'label1')

    def create_label(self, template):
        label_data = {
            'label': 'label1',
        }
        context = {'template': template}

        s = TemplateLabelSerializer(data=label_data, context=context)
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
class TestRunLabelSerializer(TransactionTestCase):

    def testCreate(self):
        run = self.create_run()
        label = self.create_label(run)
        self.assertEqual(label.run.uuid, run.uuid)

    def testRender(self):
        run = self.create_run()
        label = self.create_label(run)
        context = {'run': run}
        label_data = RunLabelSerializer(label, context=context).data
        self.assertEqual(label_data.get('label'), 'label1')

    def create_label(self, run):
        label_data = {'label': 'label1'}
        context = {'run': run}
        s = RunLabelSerializer(data=label_data, context=context)
        s.is_valid(raise_exception=True)
        return s.save()

    def create_run(self):
        with self.settings(TEST_DISABLE_ASYNC_DELAY=True):
            s = TemplateSerializer(data=fixtures.templates.step_a)
            s.is_valid(raise_exception=True)
            template = s.save()
            run = create_run_from_template(template)
        return run


class TestDataLabelSerializer(TestCase):

    def testCreate(self):
        file = self.create_file()
        label = self.create_label(file)
        self.assertEqual(label.data_object.uuid, file.uuid)
        
    def create_file(self):
        data = fixtures.data_objects.file_data_object
        s = DataObjectSerializer(data=data)
        s.is_valid(raise_exception=True)
        return s.save()

    def create_label(self, file):
        label_data = {'label': 'label1'}
        context = {'data_object': file}
        s = DataLabelSerializer(data=label_data, context=context)
        s.is_valid(raise_exception=True)
        return s.save()
