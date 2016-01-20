from django.test import TestCase
from django.db import models
from django.core.exceptions import ValidationError 
import datetime
from django.utils import timezone
import json
import hashlib

from immutable.models import *
from immutable.test.models import *
from immutable import helpers
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
        model.to_obj()
        self.assertEqual(model.listofchildren.count(), 2)

    def testCreateWithEmptyList(self):
        model_json = '{"listofchildren": []}'
        model = SampleMutableParent.create(model_json)
        self.assertEqual(model.listofchildren.count(), 0)

    def testCreateWithListOfChildrenReverseForeignKey(self):
        model_json = '{"listofchildren_foreignkey": [{"name": "ishmael"}, {"name": "jake"}]}'
        model = SampleMutableParent.create(model_json)
        self.assertEqual(model.listofchildren_foreignkey.count(), 2)

    def testCreateAllFields(self):
        model_json = '{"name": "papa", "singlechild": {"name": "ishmael"}, "listofchildren": [{"name": "ishmael"}, {"name": "jake"}]}'
        model = SampleMutableParent.create(model_json)
        self.assertEqual(model.name, 'papa')
        self.assertEqual(model.singlechild.name, 'ishmael')
        self.assertEqual(model.listofchildren.count(), 2)

    def testCreateAllFieldsSorted(self):
        model_json = '{"name": "papa", "singlechild": {"name": "ishmael"}, "listofchildren": [{"name": "ishmael"}, {"name": "jake"}]}'
        model = SampleMutableParentSorted.create(model_json)
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
        update_json = helpers.obj_to_json(update_obj)
        model.update(update_json)
        self.assertEqual(model.singlechild.name, 'moby')

    def testUpdateWithListOfChildren(self):
        model_json = '{"listofchildren": [{"name": "ishmael"}]}'
        model = SampleMutableParent.create(model_json)
        update_obj = model.to_obj()
        update_obj['listofchildren'][0]['name'] = "moby"
        update_json = helpers.obj_to_json(update_obj)
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
        update_json = helpers.obj_to_json(update_obj)
        model.update(update_json)
        self.assertEqual(model.singlechild, None)

    def testNullifyListOfChildren(self):
        model_json = '{"listofchildren": [{"name": "ishmael"}]}'
        model = SampleMutableParent.create(model_json)
        update_obj = model.to_obj()
        update_obj['listofchildren'] = []
        update_json = helpers.obj_to_json(update_obj)
        model.update(update_json)
        self.assertEqual(model.listofchildren.count(), 0)

    def testShortenListOfChildren(self):
        model_json = '{"listofchildren": [{"name": "ishmael"}, {"name": "moby"}]}'
        model = SampleMutableParent.create(model_json)
        self.assertEqual(model.listofchildren.count(), 2)
        update_obj = model.to_obj()
        update_obj['listofchildren'].pop()
        update_json = helpers.obj_to_json(update_obj)
        model.update(update_json)
        self.assertEqual(model.listofchildren.count(), 1)

    def test_json_does_not_match_schema(self):
        model_json = '{"listofchildren": [{"name": "ishmael"}, {"name": "moby"}]}'
        with self.assertRaises(CouldNotFindSubclassError):
            model = SampleMutableChild.create(model_json)
        
class TestImmutableModel(TestCase):
    def setUp(self):
        child_obj = {'name': 'one'}
        parent_obj = {'child': child_obj, 'name': 'one'}
        self.child_json = helpers.obj_to_json(child_obj)
        self.parent_json = helpers.obj_to_json(parent_obj)

    def testCreateDuplicate(self):
        model = SampleImmutableChild.create(self.child_json)
        childCountBefore = SampleImmutableChild.objects.count()
        SampleImmutableChild.create(self.child_json)
        childCountAfter = SampleImmutableChild.objects.count()
        self.assertTrue(childCountBefore==1)
        self.assertEqual(childCountBefore, childCountAfter)

        self.roundTripJson(model)
        self.roundTripObj(model)

    def test_create_verify_hash(self):
        model = SampleImmutableParent.create(self.parent_json)
        clean_json = helpers.obj_to_json(
            json.loads(self.parent_json)
            )
        expected_hash = hashlib.sha256(clean_json).hexdigest()
        self.assertEqual(expected_hash, model._id)

        self.roundTripJson(model)
        self.roundTripObj(model)

    def test_hash_with_equivalent_jsons(self):
        modelA_json = '{"name":"one"}'
        modelB_json = '{ "name" : "one" }'
        modelA = SampleImmutableChild.create(modelA_json)
        modelB = SampleImmutableChild.create(modelB_json)
        self.assertEqual(modelA._id, modelB._id)

        self.roundTripJson(modelA)
        self.roundTripObj(modelA)

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

    def test_change_list_order_unsorted_field(self):
        child1_obj = {'name': 'one'}
        child2_obj = {'name': 'two'}
        parent_obj = {'childlist': [child1_obj, child2_obj], 'name': 'one'}
        parent_reverse_obj = {'childlist': [child2_obj, child1_obj], 'name': 'one'}
        parent = SampleImmutableParent.create(parent_obj)
        parent_reverse = SampleImmutableParent.create(parent_reverse_obj)
        self.assertEqual(parent._id, parent_reverse._id)

#    def test_change_list_order_sorted_field(self):
#        child1_obj = {'name': 'one'}
#        child2_obj = {'name': 'two'}
#        parent_obj = {'childlist': [child1_obj, child2_obj], 'name': 'one'}
#        parent_reverse_obj = {'childlist': [child2_obj, child1_obj], 'name': 'one'}
#        parent = SampleImmutableParentSorted.create(parent_obj)
#        parent_reverse = SampleImmutableParent.create(parent_reverse_obj)
#        self.assertFalse(parent._id==parent_reverse._id)

    def testCreateWithEmptyList(self):
        model_json = '{"childlist": []}'
        model = SampleImmutableParent.create(model_json)
        self.assertEqual(model.childlist.count(), 0)
        self.roundTripJson(model)
        self.roundTripJson(model)

    def testCreateEmtpyChild(self):
        model_json = '{"p1": {"childlist": []}}'
        model = SampleGrandparent.create(model_json)
        self.roundTripJson(model)
        self.roundTripObj(model)

    def roundTripJson(self, model):
        cls = model.__class__
        id1 = model._id
        model = cls.create(model.to_json())
        self.assertEqual(model._id, id1)

    def roundTripObj(self, model):
        cls = model.__class__
        id1 = model._id
        model = cls.create(model.to_obj())
        self.assertEqual(model._id, id1)

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
            '{"_id":"57bbc8f5f7466bac9b01c716d04ada9c0837c710d6eecf0ee1e0368c6636a809",'\
            '"daughter1_name":"the child1"},"name":"the parent"}'
        self.assertEqual(parent.to_json(), expected)

class TimeStempTest(TestCase):

    def setUp(self):
        self.model_obj = {"name": "ishmael"}

    def testDatetimeCreatedDatetimeUpdatedAutomaticallySetOnCreate(self):
        min_time = datetime.datetime.now(timezone.utc).isoformat()
        model = SampleMutableChild.create(self.model_obj)
        max_time = datetime.datetime.now(timezone.utc).isoformat()
        self.assertTrue(min_time < model.datetime_created)
        self.assertTrue(max_time > model.datetime_created)
        self.assertTrue(min_time < model.datetime_updated)
        self.assertTrue(max_time > model.datetime_updated)

    def testDatetimeCreatedDatetimeUpdatedExplicitlySetOnCreate(self):
        datetime_created = datetime.datetime.now(timezone.utc).isoformat()
        datetime_updated = datetime.datetime.now(timezone.utc).isoformat()
        before_update = datetime.datetime.now(timezone.utc).isoformat()
        self.model_obj.update({'datetime_created': datetime_created,
                          'datetime_updated': datetime_updated})
        model = SampleMutableChild.create(self.model_obj)
        after_update = datetime.datetime.now(timezone.utc).isoformat()

        self.assertEqual(model.datetime_created, datetime_created)
        self.assertTrue(model.datetime_updated > before_update)
        self.assertTrue(model.datetime_updated < after_update)

    def testAutoSetDatetimeUpdated(self):
        time1 = datetime.datetime.now(timezone.utc).isoformat()
        model = SampleMutableChild.create(self.model_obj)
        time2 = datetime.datetime.now(timezone.utc).isoformat()
        model.update({'name': 'queequeg'})
        time3 = datetime.datetime.now(timezone.utc).isoformat()
        
        self.assertTrue(time2 < model.datetime_updated)
        self.assertTrue(time3 > model.datetime_updated)

        self.assertTrue(time1 < model.datetime_created)
        self.assertTrue(time2 > model.datetime_created)


    # Try to explicitly set datetime_created and _updated after object exists. Verify exception.

    # Verify exception when USE_TZ==False

class TestBooleanField(TestCase):
    def test_field(self):
        model_in = {'is_raining': True}
        model = BooleanModel.create(model_in)
        model_out = model.to_obj()
        self.assertEqual(model_in['is_raining'], model_out['is_raining'])
