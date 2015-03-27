from django.test import TestCase
from apps.pipelines import models as appmodels
import jsonschema
import json
import os

class PipelineTestCase(TestCase):

    TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'testdata')

    def setUp(self):

        with open(os.path.join(self.TEST_DATA_DIR, 'pipeline_flat.json')) as f:
            self.data_json_flat = json.load(f)

        with open(os.path.join(self.TEST_DATA_DIR, 'pipeline_nested.json')) as f:
            self.data_json_nested = json.load(f)

        with open(os.path.join(self.TEST_DATA_DIR, 'pipeline_invalid.json')) as f:
            self.data_json_invalid = json.load(f)

    def test_validate_data_json_with_no_links(self):
        appmodels.Pipeline._validate_data_json_with_no_links(self.data_json_nested)
        with self.assertRaises(jsonschema.ValidationError):
            appmodels.Pipeline._validate_data_json_with_no_links(self.data_json_invalid)
        with self.assertRaises(jsonschema.ValidationError):
            # Will not accept data with links
            appmodels.Pipeline._validate_data_json_with_no_links(self.data_json_flat)

    def test_validate_data_json_with_links(self):
        appmodels.Pipeline._validate_data_json_with_links(self.data_json_flat)
        # Should still accept nested data with no links
        appmodels.Pipeline._validate_data_json_with_links(self.data_json_nested)
        with self.assertRaises(jsonschema.ValidationError):
            appmodels.Pipeline._validate_data_json_with_links(self.data_json_invalid)
            




