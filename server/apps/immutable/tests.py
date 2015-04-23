"""

from django.test import TestCase
from django.db import models
import json

from .models import _Immutable

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
#
# m = ModelWithNoRelations.create(data_json) 
# Verify that m._id = hashlib.sha256(data_json).hexdigest() 
# Verify that ModelWithNoRelations.get_by_id(hashlib.sha256(data_json).hexdigest()) returns the model
# Edit a field on m and call m.save(). Verify that both the original model and the edited model now exist.
# Verify that m._json matches data_json, but standardized (keys sorted, spacing standardized)
#
# Negative tests
# Create model with invalid JSON
# Create model with schema that does not match this model (models can use jsonschema to validate)
# Edit the JSON schema so that it no longer matches the ID. Verify that the clean() method fails to validate.
#
# Model with relations:
# Create model where child is nested in input json
#   { "child": {"child_property": "x"}}
# or
#   { "children": [{"child_property": "x"},
#                  {"child_property": "y"}]}
# Verify that parent and children are created
# Modify one of the children and save. Verify that parent is unchanged.
# 
# Negative tests
# Edit the child definition in the JSON schema without changing the ForeignKey for that child. Verify that the clean() method fails to validate.

