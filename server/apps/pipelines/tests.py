from django.test import TestCase
from apps.pipelines import models as appmodels
from apps.pipelines.helpers import constant_substitution
from apps.pipelines.helpers import link_resolution
from apps.pipelines.helpers import strip_keys
import jsonschema
import json
import os

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'testdata')

class PipelineTestCase(TestCase):

    def setUp(self):

        with open(os.path.join(TEST_DATA_DIR, 'pipeline_flat.json')) as f:
            self.pipeline_flat_json = f.read()
            self.pipeline_flat = json.loads(self.pipeline_flat_json)

        with open(os.path.join(TEST_DATA_DIR, 'pipeline_nested.json')) as f:
            self.pipeline_nested_json = f.read()
            self.pipeline_nested = json.loads(self.pipeline_nested_json)

        with open(os.path.join(TEST_DATA_DIR, 'pipeline_invalid.json')) as f:
            self.pipeline_invalid_json = f.read()
            self.pipeline_invalid = json.loads(self.pipeline_invalid_json)

    def test_validate_data_json_with_no_links(self):
        appmodels.Pipeline._validate_data_json_with_no_links(self.pipeline_nested)
        with self.assertRaises(jsonschema.ValidationError):
            appmodels.Pipeline._validate_data_json_with_no_links(self.pipeline_invalid)
        with self.assertRaises(jsonschema.ValidationError):
            # Will not accept data with links
            appmodels.Pipeline._validate_data_json_with_no_links(self.pipeline_flat)

    def test_validate_data_json_with_links(self):
        appmodels.Pipeline._validate_data_json_with_links(self.pipeline_flat)
        # Should still accept nested data with no links
        appmodels.Pipeline._validate_data_json_with_links(self.pipeline_nested)
        with self.assertRaises(jsonschema.ValidationError):
            appmodels.Pipeline._validate_data_json_with_links(self.pipeline_invalid)
            
#    def test_clean_and_sort_json(self):
#        appmodels.Pipeline._clean_and_sort_json(self.pipeline_flat_json)
#        appmodels.Pipeline._clean_and_sort_json(self.pipeline_nested_json)
#        with self.assertRaises(jsonschema.ValidationError):
#            appmodels.Pipeline._clean_and_sort_json(self.pipeline_invalid_json)

class ConstantSubstitutionHelperTestCase(TestCase):

    def setUp(self):
        with open(os.path.join(TEST_DATA_DIR, 'pipeline_nested.json')) as f:
            self.pipeline_nested_json = f.read()
        self.pipeline_nested = json.loads(self.pipeline_nested_json)
        with open(os.path.join(TEST_DATA_DIR, 'pipeline_nested_substituted.json')) as f:
            self.pipeline_nested_substituted_json = f.read()
        
    def testConstantSubstitituion(self):
        data_obj = constant_substitution.ConstantSubstitutionHelper.apply_constants_in_json(
            self.pipeline_nested_json)
        data_json = json.dumps(data_obj, indent=4, separators=(',',': '))
        self.assertEqual(data_json.strip(), self.pipeline_nested_substituted_json.strip())

class LinkResolutionHelperTestCase(TestCase):

    def setUp(self):
        with open(os.path.join(TEST_DATA_DIR, 'pipeline_flat_substituted.json')) as f:
            self.pipeline_flat_substituted_json = f.read()
        with open(os.path.join(TEST_DATA_DIR, 'pipeline_nested_substituted.json')) as f:
            self.pipeline_nested_substituted_json = f.read()
        
    def testLinksResolution(self):
        data_obj = link_resolution.LinkResolutionHelper().resolve_links_in_json(
            self.pipeline_flat_substituted_json)
        data_obj_minus_ids = strip_keys.StripKeys.strip_key(data_obj, 'id')
        data_json_minus_ids = json.dumps(data_obj_minus_ids, indent=4, separators=(',',': '))

        expected_json = self.pipeline_nested_substituted_json
        expected_minus_ids = strip_keys.StripKeys.strip_key_from_json(expected_json, 'id')
        expected_json_minus_ids = json.dumps(data_obj, indent=4, separators=(',',': '))

        self.assertEqual(data_json_minus_ids.strip(), expected_json_minus_ids.strip())
