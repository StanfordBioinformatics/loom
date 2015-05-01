from django.test import TestCase
from django.db import models
from django.core.exceptions import ValidationError 
import json
import hashlib

from apps.immutable.models import _Immutable
from apps.immutable.models import FlatModel
"""
class ImmutableParent(_Immutable):
    name = models.CharField(max_length=100)

class ImmutableChild(_Immutable):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(ImmutableParent, related_name='child')
    def get_class_for_key(self, key):
        classes = {'parent': ImmutableParent}
        return classes.get(key)

class ImmutableModelTest(TestCase):
    def setUp(self):
        parent1_obj = {'name': 'one'}
        parent2_obj = {'name': 'two'}
        child1_obj = {'parent': parent1_obj, 'name': 'one'}
        child2_obj = {'parent': parent2_obj, 'name': 'two'}

        self.parent1_json = json.dumps(parent1_obj)
        self.child1_json = json.dumps(child1_obj)
        self.parent2_json = json.dumps(parent2_obj)
        self.child2_json = json.dumps(child2_obj)

        self.parent1 = ImmutableParent.create(self.parent1_json)
        import pdb; pdb.set_trace()
        self.child1 = ImmutableChild.create(self.child1_json)

    def testCreateDuplicate(self):
        
        childCountBefore = ImmutableChild.objects.count()
        ImmutableChild.create(self.child1_json)
        childCountAfter = ImmutableChild.objects.count()

        self.assertTrue(childCountBefore > 0)
        self.assertEqual(childCountBefore, childCountAfter)

    def testEditRelation(self):
        parent = self.child.parent
        original_parent_id = parent.id

        parent.json = self.parent2_json
        parent.save()

        self.assertEqual(original_parent_id, self.child.parent.id)

    def testRenderJson(self):
        self.assertEqual(self.child1.get_json(), self.child1_json)


    # TODO negative tests. Invalid JSON, fields that don't exist, fields that don't exist on children.
"""

# -------------
# Notes below are a list of tests needed. This may not be complete.

# Model definitions:
# Flat models should require only this:
"""
class MyImmutableModel(_Immutable):
    validation_schema = '{"jsonschema definition goes": "here"}'
    keymap_field = {
        "field1": self.field1,
        "field2": self.field2,
    }
    field1 = models.CharField()
    field2 = models.BooleanField()
"""


# Models with relationships should be like this:
"""
class MyImmutableModel(_Immutable):
    validation_schema = '{"jsonschema definition goes": "here"}' # No need to validate children. They will be validated in their own constructors.
    keymap_field = {
        "field1": self.field1,
        "field2": self.field2,
    }
    keymap_has_one = {
        "child1": self.child1
    }
    keymap_has_many = {
        "children2": self.child2
    }
    field1 = models.CharField()
    field2 = models.BooleanField()
    child1 = models.ForeignKey(Child1)
    child2 = models.ManyToMany(Child2)
"""
# Even better, can we get rid of the keymaps? We can look up fields by name,
# and we can look up ForeignKey and ManyToMany fields by related_name
#    
# Tests:
# 
# Flat model with no children:
# moves to models.py
#class FlatModel(_Immutable):
#    validation_schema = '{"jsonschema definition goes": "here"}'
#    field1 = models.CharField(max_length=256)
#    field2 = models.CharField(max_length=256)

'''
class TestFlatImmutableObject(TestCase):
    data_json='{"field1":"value1","field2":"value2"}' #in standard format
    data_json_nonstandard='{"field2": "value2", "field1": "value1"}'

    def test_create_verify_hash(self):
        flat_model = FlatModel.create(self.data_json) #create would call validation
        expected_hash = hashlib.sha256(self.data_json).hexdigest()
        self.assertEqual(expected_hash, flat_model._id)

    def test_create_duplicate_entry(self):
        flat_model = FlatModel.create(self.data_json) 
        count1 = FlatModel.objects.count()
        self.assertGreater(count1, 0)

        flat_model2 = FlatModel.create(self.data_json) 
        count2 = FlatModel.objects.count()
        self.assertEqual(count1, count2)

        self.assertEqual(flat_model1._id, flat_model2._id)

    def test_create_with_nonstandard_json(self):
        flat_model = FlatModel.create(self.data_json_nonstandard)
        expected_hash = hashlib.sha256(self.data_json).hexdigest() #hash should be based on standard json
        self.assertEqual(expected_hash, flat_model._id)

    def test_get_by_id(self):
        flatmodel = FlatModel.create(self.data_json)
        flatmodel.save();
        expected_id = hashlib.sha256(self.data_json).hexdigest()
        entry = FlatModel.objects.get(_id=expected_id)
        self.assertIsNotNone(entry)

    def test_raises_error_on_save(self):
        model = FlatModel.create(self.data_json)
        with self.assertRaises(Exception):
            model.save()

    def test_invalid_json(self):
        bad_json = '{oops this is invalid}'
        with self.assertRaises(ValidationError):
            FlatModel.create(bad_json)

    def test_edit_json_changes_primary_key(self):
        model=FlatModel.create(self.data_json)
        original_hash = model._id
        new_json = '{"field1":"new value","field2":"another new value"}' #in standard format
        model._json = new_json
        model.save()
        new_hash = model._id
        expected_hash = hashlib.sha256(new_json).hexdigest()
        self.assertNotEqual(original_hash, new_hash)
        self.assertEqual(model._id, expected_hash)

    def test_clean_fails_if_json_is_changed(self):
        model = FlatModel.create(self.data_json)
        original_hash = model._id
        new_json = '{"field1":"new value","field2":"another new value"}' #in standard format
        model._json = new_json
        with self.assertRaises(ValidationError):
            model.clean()

    def test_invalid_for_json_schema(self):
        bad_json='{"field1":"value1","field2000":"value2"}'
        with self.assertRaises(ValidationError):
            FlatModel.create(bad_json)
'''

# Model with relations:
#Create model where child is nested in input json
#   { "child": {"child_property": "x"}}
#or
#   { "children": [{"child_property": "x"},
#                  {"child_property": "y"}]}
# Verify that parent and children are created
# Modify one of the children and save. Verify that parent is unchanged.
# 
# Negative tests
# Edit the child definition in the JSON schema without changing the ForeignKey for that child. Verify that the clean() method fails to validate.

