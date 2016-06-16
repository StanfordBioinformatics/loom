from django.test import TestCase
from django.db import models
from django.core.exceptions import ValidationError 
import datetime
from django.utils import timezone
import json
import hashlib

from universalmodels.models import *
from universalmodels.test.models import *
from universalmodels import helpers
from django.core.exceptions import FieldDoesNotExist


class TestNonrelationFields(TestCase):

    def testJsonField(self):
        model = NonRelationFieldsInstanceModel.create({
            'json_field': {"customdata": "customvalue"},
            'boolean_field': True,
            'char_field': 'characters',
            'int_field': 3
        })
        self.assertEqual(model.json_field['customdata'], 'customvalue')
        self.assertEqual(model.char_field, 'characters')
        self.assertEqual(model.boolean_field, True)
        self.assertEqual(model.int_field, 3)

        
class TestInstanceModelRelations(TestCase):

    # One to One
    
    def testNegOneToOneScalar(self):
        with self.assertRaises(InvalidInputTypeError):
            model = SampleInstanceModelParent.create({'onetoonechild': 'value'})

    def testNegOneToOneList(self):
        with self.assertRaises(InvalidInputTypeError):
            model = SampleInstanceModelParent.create({'onetoonechild': []})

    def testOneToOneDict(self):
        parent = SampleInstanceModelParent.create({'name': 'parent', 'onetoonechild': {'name': 'onlychild'}})
        self.assertTrue(parent.onetoonechild.name == 'onlychild')

    def testOneToOneNull(self):
        model = SampleInstanceModelParent.create({'onetoonechild': None})
        self.assertIsNone(model.onetoonechild)
        
    def testNegOneToOneRevers(self):
        with self.assertRaises(ParentNestedInChildError):
            child = SampleInstanceModelChild.create({'name': 'child', 'parent': {'name': 'parent'}})
            
    # One to Many
            
    def testNegOneToManyScalar(self):
        with self.assertRaises(InvalidInputTypeError):
            parent = SampleInstanceModelParent.create({
                'name': 'parent',
                'onetomanychildren': 'children'
            })

    def testOneToManyListOfDicts(self):
        parent = SampleInstanceModelParent.create({
            'name': 'parent',
            'onetomanychildren': [
                {'name': 'twin1'},
                {'name': 'twin2'}
            ]})
        self.assertTrue(parent.onetomanychildren.first().name == 'twin1')
        self.assertTrue(parent.onetomanychildren.last().name == 'twin2')

    def testNegOneToManyListOfScalars(self):
        with self.assertRaises(InvalidInputTypeError):
            parent = SampleInstanceModelParent.create({
                'name': 'parent',
                'onetomanychildren': [
                    'twin1',
                    'twin2'
                ]})

    def testNegOneToManyDict(self):
        with self.assertRaises(InvalidInputTypeError):
            parent = SampleInstanceModelParent.create({
                'name': 'parent',
                'onetomanychildren': {'rose': 'bud'}
            })

    def testOneToManyNull(self):
        parent = SampleInstanceModelParent.create({
            'name': 'parent',
            'onetomanychildren': None
            })
        self.assertEqual(parent.onetomanychildren.count(), 0)

    def testNegOneToManyReverse(self):
        with self.assertRaises(ParentNestedInChildError):
            child = SampleInstanceModelChild2.create(
                {'name': 'child',
                 'parent': {'name': 'parent'}
                })

    # Many to Many

    def testNegManyToManyScalar(self):
        with self.assertRaises(InvalidInputTypeError):
            parent = SampleInstanceModelParent.create({
                'name': 'parent',
                'manytomanychildren': 'children'})
            
    def testManyToManyListOfDicts(self):
        parent = SampleInstanceModelParent.create({
            'name': 'parent',
            'manytomanychildren': [
                {'name': 'twin1'},
                {'name': 'twin2'}
            ]})
        self.assertTrue(parent.manytomanychildren.first().name == 'twin1')
        self.assertTrue(parent.manytomanychildren.last().name == 'twin2')

    def testNegManyToManyListOfScalars(self):
        with self.assertRaises(InvalidInputTypeError):
            parent = SampleInstanceModelParent.create({
                'name': 'parent',
                'manytomanychildren': [
                    'twin1',
                    'twin2'
                ]})

    def testManyToManyEmptyList(self):
        model_json = '{"manytomanychildren": []}'
        model = SampleInstanceModelParent.create(model_json)
        self.assertEqual(model.manytomanychildren.count(), 0)

    def testNegManyToManyDict(self):
        with self.assertRaises(InvalidInputTypeError):
            parent = SampleInstanceModelParent.create({
                'name': 'parent',
                'manytomanychildren': {'twin1': 'joe'}
            })

    def testManyToManyNull(self):
        model_json = '{"manytomanychildren": null}'
        model = SampleInstanceModelParent.create(model_json)
        self.assertEqual(model.manytomanychildren.count(), 0)
            
    def testNegManyToManyReverse(self):
        with self.assertRaises(ParentNestedInChildError):
            child = SampleInstanceModelChild3.create(
                {'name': 'child',
                 'parents': {'name': 'parent'}
                })

    # Many to One (ForeignKey)
    def testNegForeignKeyScalar(self):
        with self.assertRaises(InvalidInputTypeError):
            model = SampleInstanceModelParent.create({'foreignkeychild': 'value'})

    def testNegForeignKeyList(self):
        with self.assertRaises(InvalidInputTypeError):
            model = SampleInstanceModelParent.create({'foreignkeychild': []})

    def testForeignKeyDict(self):
        parent = SampleInstanceModelParent.create({
            'name': 'parent',
            'foreignkeychild': {
                'name': 'foreignkeychild',
            }
        })
        self.assertTrue(parent.foreignkeychild.name == 'foreignkeychild')

    def testForeignKeyNull(self):
        model = SampleInstanceModelParent.create({'foreignkeychild': None})
        self.assertIsNone(model.onetoonechild)
        
    def testNegForeignKeyReverse(self):
        with self.assertRaises(ParentNestedInChildError):
            child = SampleInstanceModelChild4.create({'name': 'child', 'parents': [{'name': 'parents'}]})
            
    # All
        
    def testCreateAllFields(self):
        parent = SampleInstanceModelParent.create({
            'name': 'parent',
            'onetoonechild': {'name': 'onlychild'},
            'onetomanychildren': [
                {'name': 'twin1'},
                {'name': 'twin2'}
            ],
            'manytomanychildren': [
                {'name': 'twin1'},
                {'name': 'twin2'}
            ],
            'foreignkeychild': {'name': 'foreignkeychild'}
        })

        self.assertEqual(parent.name, 'parent')
        self.assertEqual(parent.onetoonechild.name, 'onlychild')
        self.assertEqual(parent.onetomanychildren.first().name, 'twin1')
        self.assertEqual(parent.onetomanychildren.count(), 2)
        self.assertEqual(parent.manytomanychildren.first().name, 'twin1')
        self.assertEqual(parent.manytomanychildren.count(), 2)
        self.assertEqual(parent.foreignkeychild.name, 'foreignkeychild')


class TestImmutableModelRelations(TestCase):

    # Many to Many

    def testNegManyToManyScalar(self):
        with self.assertRaises(InvalidInputTypeError):
            parent = SampleImmutableParent.create({
                'name': 'parent',
                'manytomanychildren': 'children'})
            
    def testManyToManyListOfDicts(self):
        parent = SampleImmutableParent.create({
            'name': 'parent',
            'manytomanychildren': [
                {'name': 'twin1'},
                {'name': 'twin2'}
            ]})
        self.assertTrue(parent.manytomanychildren.first().name == 'twin1')
        self.assertTrue(parent.manytomanychildren.last().name == 'twin2')

    def testNegManyToManyListOfScalars(self):
        with self.assertRaises(InvalidInputTypeError):
            parent = SampleImmutableParent.create({
                'name': 'parent',
                'manytomanychildren': [
                    'twin1',
                    'twin2'
                ]})

    def testManyToManyEmptyList(self):
        model_json = '{"manytomanychildren": []}'
        model = SampleImmutableParent.create(model_json)
        self.assertEqual(model.manytomanychildren.count(), 0)

    def testNegManyToManyDict(self):
        with self.assertRaises(InvalidInputTypeError):
            parent = SampleImmutableParent.create({
                'name': 'parent',
                'manytomanychildren': {'twin1': 'joe'}
            })

    def testManyToManyNull(self):
        model_json = '{"manytomanychildren": null}'
        model = SampleImmutableParent.create(model_json)
        self.assertEqual(model.manytomanychildren.count(), 0)
            
    def testNegManyToManyReverse(self):
        with self.assertRaises(ParentNestedInChildError):
            child = SampleImmutableChild3.create(
                {'name': 'child',
                 'parents': {'name': 'parent'}
                })

    # Many to One (ForeignKey)
    def testNegForeignKeyScalar(self):
        with self.assertRaises(InvalidInputTypeError):
            model = SampleImmutableParent.create({'foreignkeychild': 'value'})

    def testNegForeignKeyList(self):
        with self.assertRaises(InvalidInputTypeError):
            model = SampleImmutableParent.create({'foreignkeychild': []})

    def testForeignKeyDict(self):
        parent = SampleImmutableParent.create({
            'name': 'parent',
            'foreignkeychild': {
                'name': 'foreignkeychild',
            }
        })
        self.assertTrue(parent.foreignkeychild.name == 'foreignkeychild')

    def testForeignKeyNull(self):
        model = SampleImmutableParent.create({'foreignkeychild': None})
        self.assertIsNone(model.foreignkeychild)
        
    def testNegForeignKeyReverse(self):
        with self.assertRaises(ParentNestedInChildError):
            child = SampleImmutableChild4.create({'name': 'child', 'parents': [{'name': 'parent'}]})
            
    # All
        
    def testCreateAllFields(self):
        parent = SampleImmutableParent.create({
            'name': 'parent',
            'manytomanychildren': [
                {'name': 'twin1'},
                {'name': 'twin2'}
            ],
            'foreignkeychild': {'name': 'foreignkeychild'}
        })

        self.assertEqual(parent.name, 'parent')
        self.assertEqual(parent.manytomanychildren.first().name, 'twin1')
        self.assertEqual(parent.manytomanychildren.count(), 2)
        self.assertEqual(parent.foreignkeychild.name, 'foreignkeychild')


class TestInstanceModelRender(TestCase):

    def testToJson(self):
        parent = SampleInstanceModelParent.create({
            'name': 'parent',
            'onetoonechild': {'name': 'onlychild'},
            'onetomanychildren': [
                {'name': 'twin1'},
                {'name': 'twin2'}
            ],
            'manytomanychildren': [
                {'name': 'twin1'},
                {'name': 'twin2'}
            ],
            'foreignkeychild': {'name': 'foreignkeychild'}
        })

        model_json = parent.to_json()
        model_struct = json.loads(model_json)
        
        self.assertEqual(model_struct['name'], 'parent')
        self.assertEqual(model_struct['onetoonechild']['name'], 'onlychild')
        self.assertEqual(model_struct['onetomanychildren'][0]['name'], 'twin1')
        self.assertEqual(len(model_struct['onetomanychildren']), 2)
        self.assertEqual(model_struct['manytomanychildren'][0]['name'], 'twin1')
        self.assertEqual(len(model_struct['manytomanychildren']), 2)
        self.assertEqual(model_struct['foreignkeychild']['name'], 'foreignkeychild')

    def testToStruct(self):
        parent = SampleInstanceModelParent.create({
            'name': 'parent',
            'onetoonechild': {'name': 'onlychild'},
            'onetomanychildren': [
                {'name': 'twin1'},
                {'name': 'twin2'}
            ],
            'manytomanychildren': [
                {'name': 'twin1'},
                {'name': 'twin2'}
            ],
            'foreignkeychild': {'name': 'foreignkeychild'}
        })

        model_struct = parent.to_struct()
        
        self.assertEqual(model_struct['name'], 'parent')
        self.assertEqual(model_struct['onetoonechild']['name'], 'onlychild')
        self.assertEqual(model_struct['onetomanychildren'][0]['name'], 'twin1')
        self.assertEqual(len(model_struct['onetomanychildren']), 2)
        self.assertEqual(model_struct['manytomanychildren'][0]['name'], 'twin1')
        self.assertEqual(len(model_struct['manytomanychildren']), 2)
        self.assertEqual(model_struct['foreignkeychild']['name'], 'foreignkeychild')


class TestImmutableModelRender(TestCase):

    def testToJson(self):
        parent = SampleImmutableParent.create({
            'name': 'parent',
            'manytomanychildren': [
                {'name': 'twin1'},
                {'name': 'twin2'}
            ],
            'foreignkeychild': {'name': 'foreignkeychild'}
        })

        model_json = parent.to_json()
        model_struct = json.loads(model_json)
        
        self.assertEqual(model_struct['name'], 'parent')
        self.assertEqual(model_struct['manytomanychildren'][0]['name'], 'twin1')
        self.assertEqual(len(model_struct['manytomanychildren']), 2)
        self.assertEqual(model_struct['foreignkeychild']['name'], 'foreignkeychild')

    def testToStruct(self):
        parent = SampleImmutableParent.create({
            'name': 'parent',
            'manytomanychildren': [
                {'name': 'twin1'},
                {'name': 'twin2'}
            ],
            'foreignkeychild': {'name': 'foreignkeychild'}
        })

        model_struct = parent.to_struct()
        
        self.assertEqual(model_struct['name'], 'parent')
        self.assertEqual(model_struct['manytomanychildren'][0]['name'], 'twin1')
        self.assertEqual(len(model_struct['manytomanychildren']), 2)
        self.assertEqual(model_struct['foreignkeychild']['name'], 'foreignkeychild')


class TestInstanceModelUpdate(TestCase):
        
    # Update method - Nonrelation field

    def testUpdateNonrelationField(self):
        model_json = '{"name": "ishmael"}'
        model = SampleInstanceModelChild.create(model_json)
        update_json = '{"name": "moby"}'
        model.update(update_json)
        self.assertEqual(model.name, 'moby')

    def testNegUpdateNonrelationFieldInvalidInput(self):
        model_json = '{"name": "ishmael"}'
        model = SampleInstanceModelChild.create(model_json)
        update_json = '{"name": ["moby"]}'
        with self.assertRaises(InvalidInputTypeError):
            model.update(update_json)

    def testUpdateNonrelationFieldFromStruct(self):
        model_json = '{"name": "ishmael"}'
        model = SampleInstanceModelChild.create(model_json)
        update_struct = {"name": "moby"}
        model.update(update_struct)
        self.assertEqual(model.name, 'moby')

    # Update method - OneToOne

    def testUpdateOneToOneDictInput(self):
        model = SampleInstanceModelParent.create('{"onetoonechild": {"name": "ishmael"}}')
        model.update('{"onetoonechild": {"name": "moby"}}')
        self.assertEqual(model.onetoonechild.name, 'moby')
    
    def testUpdateOneToOneNullInput(self):
        model = SampleInstanceModelParent.create('{"onetoonechild": {"name": "ishmael"}}')
        model.update('{"onetoonechild": null}')
        self.assertEqual(model.onetoonechild, None)
        
    def testNegUpdateOneToOneInvalidInput(self):
        model = SampleInstanceModelParent.create('{"onetoonechild": {"name": "ishmael"}}')
        with self.assertRaises(InvalidInputTypeError):
            model.update('{"onetoonechild": [{"name": "ishmael"}]}')

    # Update method - OneToMany

    def testUpdateOneToManyListInput(self):
        model = SampleInstanceModelParent.create('{"onetomanychildren": [{"name": "jack"}, {"name": "jill"}]}')
        model.update('{"onetomanychildren": [{"name": "jack"}]}')
        self.assertEqual(model.onetomanychildren.count(), 1)
        
    def testUpdateOneToManyNullInput(self):
        model = SampleInstanceModelParent.create('{"onetomanychildren": [{"name": "jack"}, {"name": "jill"}]}')
        model.update('{"onetomanychildren": null}')
        self.assertEqual(model.onetomanychildren.count(), 0)

    def testUpdateOneToManyEmptyListInput(self):
        model = SampleInstanceModelParent.create('{"onetomanychildren": [{"name": "jack"}, {"name": "jill"}]}')
        model.update('{"onetomanychildren": []}')
        self.assertEqual(model.onetomanychildren.count(), 0)
        
    def testNegUpdateOneToManyInvalidInput(self):
        model = SampleInstanceModelParent.create('{"onetomanychildren": [{"name": "ishmael"}]}')
        with self.assertRaises(InvalidInputTypeError):
            model.update('{"onetomanychildren": "invalid"}')

    # Update method - ManyToMany

    def testUpdateManyToManyListInput(self):
        model = SampleInstanceModelParent.create('{"manytomanychildren": [{"name": "jack"}, {"name": "jill"}]}')
        model.update('{"manytomanychildren": [{"name": "jack"}]}')
        self.assertEqual(model.manytomanychildren.count(), 1)
        
    def testUpdateManyToManyNullInput(self):
        model = SampleInstanceModelParent.create('{"manytomanychildren": [{"name": "jack"}, {"name": "jill"}]}')
        model.update('{"manytomanychildren": null}')
        self.assertEqual(model.manytomanychildren.count(), 0)

    def testUpdateManyToManyEmptyListInput(self):
        model = SampleInstanceModelParent.create('{"manytomanychildren": [{"name": "jack"}, {"name": "jill"}]}')
        model.update('{"manytomanychildren": []}')
        self.assertEqual(model.manytomanychildren.count(), 0)
        
    def testNegUpdateManyToManyInvalidInput(self):
        model = SampleInstanceModelParent.create('{"manytomanychildren": [{"name": "ishmael"}]}')
        with self.assertRaises(InvalidInputTypeError):
            model.update('{"manytomanychildren": "invalid"}')

    # Update method - One to One (ForeignKey)

    def testUpdateForeignKeyDictInput(self):
        model = SampleInstanceModelParent.create('{"foreignkeychild": {"name": "ishmael"}}')
        model.update('{"foreignkeychild": {"name": "moby"}}')
        self.assertEqual(model.foreignkeychild.name, 'moby')
    
    def testUpdateForeignKeyNullInput(self):
        model = SampleInstanceModelParent.create('{"foreignkeychild": {"name": "ishmael"}}')
        model.update('{"foreignkeychild": null}')
        self.assertEqual(model.foreignkeychild, None)
        
    def testNegUpdateForeignKeyInvalidInput(self):
        model = SampleInstanceModelParent.create('{"foreignkeychild": {"name": "ishmael"}}')
        with self.assertRaises(InvalidInputTypeError):
            model.update('{"foreignkeychild": [{"name": "ishmael"}]}')


class TestIllegalRelations(TestCase):

    def testNegOneToOneImmutable(self):
        with self.assertRaises(IllegalRelationError):
            model = SampleImmutableParentInvalid.create('{"onetoonechild": {"name": "ishmael"}}')

    def testNegOneToManyImmutable(self):
        with self.assertRaises(IllegalRelationError):
            model = SampleImmutableParentInvalid.create('{"onetomanychildren": [{"name": "ishmael"}]}')

    def testNegImmutableParentInstanceChild(self):
        pass

class TestInstanceModel(TestCase):

    def testJsonDoesNotMatchSchema(self):
        model_json = '{"badfieldname": "info"}'
        with self.assertRaises(CouldNotFindSubclassError):
            model = SampleInstanceModelChild.create(model_json)

    def testCreateDuplicate(self):
        child_json = {"name": "child"}
        model = SampleImmutableChild.create(child_json)
        childCountBefore = SampleImmutableChild.objects.count()
        SampleImmutableChild.create(child_json)
        childCountAfter = SampleImmutableChild.objects.count()
        self.assertTrue(childCountBefore==1)
        self.assertEqual(childCountBefore, childCountAfter)

    def testCreateVerifyHash(self):
        parent_struct = {'foreignkeychild': {'name': 'Joe'}}
        model = SampleImmutableParent.create(parent_struct)
        clean_parent_json = helpers.struct_to_json(parent_struct)
        expected_hash = hashlib.sha256(clean_parent_json).hexdigest()
        self.assertEqual(expected_hash, model._id)

    def testHashWithEquivalentJsons(self):
        modelA_json = '{"name":"one"}'
        modelB_json = '{ "name" : "one" }'
        modelA = SampleImmutableChild.create(modelA_json)
        modelB = SampleImmutableChild.create(modelB_json)
        self.assertEqual(modelA._id, modelB._id)

    def testRaisesErrorOnSave(self):
        model = SampleImmutableChild.create({'name': 'Joe'})
        with self.assertRaises(NoSaveAllowedError):
            model.save()

    def testInvalidJson(self):
        bad_json = '{oops this is invalid}'
        with self.assertRaises(InvalidJsonError):
            SampleImmutableChild.create(bad_json)

    def testImmutableContainsInstanceRaisesError(self):
        with self.assertRaises(InstanceModelChildError):
            model = BadImmutableParent.create({'child': {'name': 'Child of bad parent'}})

#    def roundTripJson(self, model):
#        cls = model.__class__
#        id1 = model._id
#        model = cls.create(model.to_json())
#        self.assertEqual(model._id, id1)

#    def roundTripStruct(self, model):
#        cls = model.__class__
#        id1 = model._id
#        model = cls.create(model.to_struct())
#        self.assertEqual(model._id, id1)


class TestInheritance(TestCase):

    def testAbstractInheritance(self):
        parent_json = '{"name": "the parent", "son1": {"name": "the child1", "son1detail": "moredata"}}'
        parent = ParentOfAbstract.create(parent_json)
        self.assertEqual(parent.son1.name, "the child1")

    def testReloadWithAbstractInheritance(self):
        parent_json = '{"name": "the parent", "son1": {"name": "the child1", "son1detail": "moredata"}}'
        parent = ParentOfAbstract.create(parent_json)
        parent_reloaded = ParentOfAbstract.objects.get(_id=parent._id)
        self.assertEqual(parent_reloaded.son1.name, "the child1")

    def testReloadWithMultitableInheritance(self):
        parent_json = '{"name": "the parent", "child": {"daughter1_name": "the child1"}}'
        parent = ParentOfMultiTable.create(parent_json)
        parent_reloaded = ParentOfMultiTable.get_by_id(parent._id)
        self.assertEqual(parent_reloaded.child.get('daughter1_name'), "the child1")
        
    def testMultiTableInheritance(self):
        parent1_json = '{"name": "the parent", "child": {"daughter1_name": "the child1"}}'
        parent2_json = '{"name": "the parent", "child": {"daughter2_name": "the child2"}}'

        parent1 = ParentOfMultiTable.create(parent1_json)
        parent2 = ParentOfMultiTable.create(parent2_json)

        self.assertEqual(parent1.child.daughter1_name, "the child1")
        self.assertEqual(parent2.child.daughter2_name, "the child2")

    def testRenderAbstractModels(self):
        abstract_parent_json = '{"name": "the parent", "son1": {"name": "the child1", "son1detail": "moredata"}}'
        parent = ParentOfAbstract.create(abstract_parent_json)
        expected = '{"_class":"ParentOfAbstract",'\
                   '"_id":"914405d3925bbe9783a8864e9e3ba54160ba2dd248a54db45cd0d838675985e8",'\
                   '"name":"the parent","son1":{"_class":"Son1","_id":'\
                   '"b6254f5c3037194ae0e031e47b47c341d8f9da3c9cfdcc70c536366a91f46ded","name":'\
                   '"the child1","son1detail":"moredata"}}'
        self.assertEqual(parent.to_json(), expected)
        
    def testRenderMultitableModels(self):
        multitable_parent_json = '{"child":{"daughter1_name":"the child1"},"name":"the parent"}'
        parent = ParentOfMultiTable.create(multitable_parent_json)
        expected = '{"_class":"ParentOfMultiTable","_id":'\
                   '"a33306f11667fb440530ca0b2d18732221786cc9bbd33edfa684f9cef028798b","child":{"_class":'\
                   '"Daughter1","_id":"57bbc8f5f7466bac9b01c716d04ada9c0837c710d6eecf0ee1e0368c6636a809",'\
                   '"daughter1_name":"the child1"},"name":"the parent"}'
        self.assertEqual(parent.to_json(), expected)
        
class TestTimeStamps(TestCase):

    def setUp(self):
        self.model_struct = {"name": "ishmael"}

    def testDatetimeCreatedDatetimeUpdatedAutomaticallySetOnCreate(self):
        min_time = datetime.datetime.now(timezone.utc)
        model = SampleInstanceModelChild.create(self.model_struct)
        max_time = datetime.datetime.now(timezone.utc)
        self.assertTrue(min_time < model.datetime_created)
        self.assertTrue(max_time > model.datetime_created)
        self.assertTrue(min_time < model.datetime_updated)
        self.assertTrue(max_time > model.datetime_updated)

    def testDatetimeCreatedDatetimeUpdatedExplicitlySetOnCreate(self):
        datetime_created = datetime.datetime.now(timezone.utc)
        datetime_updated = datetime.datetime.now(timezone.utc)
        before_update = datetime.datetime.now(timezone.utc)
        self.model_struct.update({'datetime_created': datetime_created,
                          'datetime_updated': datetime_updated})
        model = SampleInstanceModelChild.create(self.model_struct)
        after_update = datetime.datetime.now(timezone.utc)

        self.assertEqual(model.datetime_created, datetime_created.isoformat())
        self.assertTrue(model.datetime_updated > before_update)
        self.assertTrue(model.datetime_updated < after_update)

    def testAutoSetDatetimeUpdated(self):
        time1 = datetime.datetime.now(timezone.utc)
        model = SampleInstanceModelChild.create(self.model_struct)
        time2 = datetime.datetime.now(timezone.utc)
        model.update({'name': 'queequeg'})
        time3 = datetime.datetime.now(timezone.utc)
        self.assertTrue(time2 < model.datetime_updated)
        self.assertTrue(time3 > model.datetime_updated)

        self.assertTrue(time1.isoformat() < model.datetime_created)
        self.assertTrue(time2.isoformat() > model.datetime_created)
