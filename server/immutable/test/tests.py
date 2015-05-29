from django.test import TestCase
from django.db import models
from django.core.exceptions import ValidationError 
import json
import hashlib

from immutable.models import *
from immutable.test.models import *
from django.core.exceptions import FieldDoesNotExist

class TestMutableModel(TestCase):

    def testCreateWithScalarProperty(self):
        model_json = '{"name": "ishmael"}'
        model = SampleMutableChild.create(model_json)
        self.assertEqual(model.name, 'ishmael')

    def testCreateWithDictChild(self):
        model_json = '{"singlechild": {"name": "ishmael"}}'
        model = SampleMutableParent.create(model_json)
        self.assertEqual(model.singlechild.name, 'ishmael')

    def testCreateWithListOfChildren(self):
        model_json = '{"listofchildren": [{"name": "ishmael"}, {"name": "jake"}]}'
        model = SampleMutableParent.create(model_json)
        self.assertEqual(model.listofchildren.count(), 2)

    def testCreateWithListOfChildrenReverseForeignKey(self):
        model_json = '{"listofchildren_foreignkey": [{"name": "ishmael"}, {"name": "jake"}]}'
        with self.assertRaises(ForeignKeyInChildError):
            model = SampleMutableParent.create(model_json)

    def testCreateAllFields(self):
        model_json = '{"name": "papa", "singlechild": {"name": "ishmael"}, "listofchildren": [{"name": "ishmael"}, {"name": "jake"}]}'
        model = SampleMutableParent.create(model_json)
        self.assertEqual(model.name, 'papa')
        self.assertEqual(model.singlechild.name, 'ishmael')
        self.assertEqual(model.listofchildren.count(), 2)

    def testToJson(self):
        model_json = '{"name": "papa", "singlechild": {"name": "ishmael"}, "listofchildren": [{"name": "ishmael"}, {"name": "jake"}]}'
        model = SampleMutableParent.create(model_json)
        model_json_dump = model.to_json()
        model_obj = json.loads(model_json_dump)
        self.assertEqual(model_obj['name'], 'papa')
        self.assertEqual(model_obj['singlechild']['name'], 'ishmael')
        self.assertEqual(len(model_obj['listofchildren']), 2)

    def testUpdateWithScalarProperty(self):
        model_json = '{"name": "ishmael"}'
        model = SampleMutableChild.create(model_json)

        update_json = '{"name": "moby"}'
        model.update(update_json)
        self.assertEqual(model.name, 'moby')

    def testUpdateWithDictChild(self):
        model_json = '{"singlechild": {"name": "ishmael"}}'
        model = SampleMutableParent.create(model_json)

        update_obj = model.to_obj()
        update_obj['singlechild']['name'] = "moby"
        update_json = json.dumps(update_obj)
        model.update(update_json)
        self.assertEqual(model.singlechild.name, 'moby')

    def testUpdateWithListOfChildren(self):
        model_json = '{"listofchildren": [{"name": "ishmael"}]}'
        model = SampleMutableParent.create(model_json)
        update_obj = model.to_obj()
        update_obj['listofchildren'][0]['name'] = "moby"
        update_json = json.dumps(update_obj)
        model.update(update_json)
        self.assertEqual(model.listofchildren.first().name, 'moby')

    def testNullifyScalarProperty(self):
        model_json = '{"name": "ishmael"}'
        model = SampleMutableChild.create(model_json)

        update_json = '{"name": "moby"}'
        model.update(update_json)
        self.assertEqual(model.name, 'moby')

    def testNullifyForeignKey(self):
        model_json = '{"singlechild": {"name": "ishmael"}}'
        model = SampleMutableParent.create(model_json)

        update_obj = model.to_obj()
        update_obj['singlechild'] = None
        update_json = json.dumps(update_obj)
        model.update(update_json)
        self.assertEqual(model.singlechild, None)

    def testNullifyListOfChildren(self):
        model_json = '{"listofchildren": [{"name": "ishmael"}]}'
        model = SampleMutableParent.create(model_json)
        update_obj = model.to_obj()
        update_obj['listofchildren'] = []
        update_json = json.dumps(update_obj)
        model.update(update_json)
        self.assertEqual(model.listofchildren.count(), 0)

    def testShortenListOfChildren(self):
        model_json = '{"listofchildren": [{"name": "ishmael"}, {"name": "moby"}]}'
        model = SampleMutableParent.create(model_json)
        self.assertEqual(model.listofchildren.count(), 2)
        update_obj = model.to_obj()
        update_obj['listofchildren'].pop()
        update_json = json.dumps(update_obj)
        model.update(update_json)
        self.assertEqual(model.listofchildren.count(), 1)

    def test_json_does_not_match_schema(self):
        model_json = '{"listofchildren": [{"name": "ishmael"}, {"name": "moby"}]}'
        with self.assertRaises(CouldNotFindSubclassError):
            model = SampleMutableChild.create(model_json)
        
class ImmutableModelTest(TestCase):
    def setUp(self):
        child_obj = {'name': 'one'}
        parent_obj = {'child': child_obj, 'name': 'one'}
        self.child_json = json.dumps(child_obj)
        self.parent_json = json.dumps(parent_obj)

    def testCreateDuplicate(self):
        SampleImmutableChild.create(self.child_json)
        childCountBefore = SampleImmutableChild.objects.count()
        SampleImmutableChild.create(self.child_json)
        childCountAfter = SampleImmutableChild.objects.count()
        self.assertTrue(childCountBefore > 0)
        self.assertEqual(childCountBefore, childCountAfter)

    def test_create_verify_hash(self):
        model = SampleImmutableParent.create(self.parent_json)
        clean_json = json.dumps(
            json.loads(self.parent_json),
            sort_keys=True, 
            separators=(',',':')
        )
        expected_hash = hashlib.sha256(clean_json).hexdigest()
        self.assertEqual(expected_hash, model._id)

    def test_hash_with_equivalent_jsons(self):
        modelA_json = '{"name":"one"}'
        modelB_json = '{ "name" : "one" }'
        modelA = SampleImmutableChild.create(modelA_json)
        modelB = SampleImmutableChild.create(modelB_json)
        self.assertEqual(modelA._id, modelB._id)

    def testRaisesErrorOnSave(self):
        model = SampleImmutableChild.create(self.child_json)
        with self.assertRaises(NoSaveAllowedError):
            model.save()

    def test_invalid_json(self):
        bad_json = '{oops this is invalid}'
        with self.assertRaises(InvalidJsonError):
            SampleImmutableChild.create(bad_json)

    def test_immutable_contains_mutable_raises_error(self):
        with self.assertRaises(MutableChildError):
            model = BadImmutableParent.create(self.parent_json)

class InheritanceTest(TestCase):
    def testAbstractInheritance(self):
        parent1_json = '{"name": "the parent", "child": {"son1_name": "the child1"}}'
        parent2_json = '{"name": "the parent", "child": {"son2_name": "the child2"}}'

        parent1 = ParentOfAbstract.create(parent1_json)
        parent2 = ParentOfAbstract.create(parent2_json)

        self.assertEqual(parent1.child.son1_name, "the child1")
        self.assertEqual(parent2.child.son2_name, "the child2")

    def testMultiTableInheritance(self):
        parent1_json = '{"name": "the parent", "child": {"daughter1_name": "the child1"}}'
        parent2_json = '{"name": "the parent", "child": {"daughter2_name": "the child2"}}'

        parent1 = ParentOfMultiTable.create(parent1_json)
        parent2 = ParentOfMultiTable.create(parent2_json)

        self.assertEqual(parent1.child.daughter1_name, "the child1")
        self.assertEqual(parent2.child.daughter2_name, "the child2")

    def testToAbstractModels(self):
        abstract_parent_json = '{"child":{"son1_name":"the child1"},"name":"the parent"}'
        parent = ParentOfAbstract.create(abstract_parent_json)
        expected = '{"_id":"7759b0240ed8ef1326aa05820f45f03bc4119eeb45794215b527645512969b75","child":'\
                   '{"_id":"a77b7d0e6b10c94828ab5bc6f7ffbe23d0e0fe1920429bdd64491be2f2346535","son1_name":'\
                   '"the child1"},"name":"the parent"}'
        self.assertEqual(parent.to_json(), expected)

    def testToJsonMultitableModels(self):
        multitable_parent_json = '{"child":{"daughter1_name":"the child1"},"name":"the parent"}'
        parent = ParentOfMultiTable.create(multitable_parent_json)
        expected = '{"_id":"a33306f11667fb440530ca0b2d18732221786cc9bbd33edfa684f9cef028798b","child":'\
                   '{"_id":"57bbc8f5f7466bac9b01c716d04ada9c0837c710d6eecf0ee1e0368c6636a809","daughter1_name":'\
                   '"the child1","multitablebasechild_ptr":'\
                   '{"_id":"57bbc8f5f7466bac9b01c716d04ada9c0837c710d6eecf0ee1e0368c6636a809"}},"name":"the parent"}'
        self.assertEqual(parent.to_json(), expected)
