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

"""
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
