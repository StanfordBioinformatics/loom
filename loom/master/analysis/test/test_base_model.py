from django.test import TestCase
from analysis.models.data_objects import *
from analysis.models.channels import *
from analysis.serializers.data_objects import *
from . import fixtures

"""This module tests the core functionality in 
analysis.models.base and analysis.serializers.base

We use DataObject models in these tests since they DataObjects
extend our base model classes and exhibit complex polymorphic 
inheritance, but the tests are targeting the behavior of the
base classes
"""

class TestBaseModel(TestCase):

    def testNestedPolymorphicDeserialize(self):

        # Setup - Create a model with a polymorphic relationship to child
        s = FileDataObjectSerializer(data=fixtures.data_objects.file_data_object)
        s.is_valid()
        file_data_object = s.save()

        # file_data_object.file_import is a polymorphic. Make sure we created the
        # model with the FileImport subclass (not the AbstractFileImport base class)
        # and have access to its fields.
        self.assertEqual(file_data_object.file_import.__class__.__name__, 'FileImport')
        self.assertEqual(file_data_object.file_import.note, fixtures.data_objects.file_data_object['file_import']['note'])

    def testAccessPolymorphicChildFromParent(self):

        # Setup - Create a model with a polymorphic relationship to child.
        # Re-load it from the database
        s = FileDataObjectSerializer(data=fixtures.data_objects.file_data_object)
        s.is_valid()
        file_data_object = s.save()
        reloaded = FileDataObject.objects.get(id=file_data_object.id)

        # Make sure accessor for child returns subclass, not base class
        self.assertEqual(reloaded.file_import.__class__.__name__, 'FileImport')
        self.assertEqual(reloaded.file_import.note, fixtures.data_objects.file_data_object['file_import']['note'])

    def testUpdateNestedModelCharField(self):
        # Setup - create a model with CharField
        s = FileContentSerializer(data=fixtures.data_objects.file_content)
        s.is_valid()
        file_content = s.save()
        file_content_id = file_content.id

        # Update char field on exiting model
        new_filename = 'new_filename'
        data = {
            'filename': new_filename
        }
        s = FileContentSerializer(file_content, data=data, partial=True)
        s.is_valid()
        s.save()

        # Load from DB and verify that field was updated
        self.assertEqual(FileContent.objects.get(id=file_content_id).filename, new_filename)

    def testUpdateNestedModelUpdateForeignKey(self):
        # Setup - create a model with ForeignKey
        s = FileContentSerializer(data=fixtures.data_objects.file_content)
        s.is_valid()
        file_content = s.save()
        file_content_id = file_content.id
        unnamed_file_content_id = file_content.unnamed_file_content.id

        # Update child model related by foreignkey
        new_hash_value = 'new_hash_value'
        data = {
            'id': file_content_id,
            'unnamed_file_content': {
                'id': unnamed_file_content_id,
                'hash_value': new_hash_value
            }
        }
        s = FileContentSerializer(file_content, data=data, partial=True)
        s.is_valid()
        new_file_content = s.save()

        # Load from DB and verify that child  was updated
        unnamed_file_content = FileContent.objects.get(id=file_content_id).unnamed_file_content

        # Primary key was not changed by update
        self.assertEqual(unnamed_file_content.id, unnamed_file_content_id)
        # Field value was set
        self.assertEqual(unnamed_file_content.hash_value, new_hash_value)
    
    def testUpdateNestedModelAddForeignKey(self):
        # Setup - create a model with ForeignKey field unassigned
        s = FileDataObjectSerializer(data={'file_import': fixtures.data_objects.file_import})
        s.is_valid()
        file_data_object = s.save()

        # Update child model related by foreignkey
        data = {'file_content': fixtures.data_objects.file_content}
        s = FileDataObjectSerializer(file_data_object, data=data, partial=True)
        s.is_valid()
        new_file_content = s.save()

        # Load from DB and verify that child  was updated
        file_data_object = FileDataObject.objects.get(id=file_data_object.id)

        self.assertEqual(file_data_object.file_content.unnamed_file_content.hash_value, fixtures.data_objects.file_content['unnamed_file_content']['hash_value'])

    def testManyToManyAddDuplicate(self):
        s = FileDataObjectSerializer(data=fixtures.data_objects.file_data_object)
        s.is_valid()
        file_data_object = s.save()
        
        channel = Channel(name='channelx')
        channel.save()

        channel.data_objects.add(file_data_object)
        channel.data_objects.add(file_data_object)
        self.assertEqual(channel.data_objects.count(), 2)

    def testManyToManyOrder(self):

        # Create models
        s1 = FileDataObjectSerializer(data=fixtures.data_objects.file_data_object)
        s1.is_valid()
        f1 = s1.save()

        s3 = FileDataObjectSerializer(data=fixtures.data_objects.file_data_object)
        s3.is_valid()
        f3 = s3.save()
        
        s2 = FileDataObjectSerializer(data=fixtures.data_objects.file_data_object)
        s2.is_valid()
        f2 = s2.save()

        channel = Channel(name='channelx')
        channel.save()

        # Create M2M relationship, add models in an order that differs from order of creation
        channel.data_objects.add(f1)
        channel.data_objects.add(f2)
        channel.data_objects.add(f3)
        flist = channel.data_objects.all()

        # Queryset order corresponds to order of adding, not creating
        self.assertEqual(flist[0].id, f1.id)
        self.assertEqual(flist[1].id, f2.id)
        self.assertEqual(flist[2].id, f3.id)

    def testRemoveDuplicateFromManyToMany(self):
        # Create models
        s = FileDataObjectSerializer(data=fixtures.data_objects.file_data_object)
        s.is_valid()
        file_data_object = s.save()
        
        channel = Channel(name='channelx')
        channel.save()

        channel.data_objects.add(file_data_object)
        channel.data_objects.add(file_data_object)
        self.assertEqual(channel.data_objects.count(), 2)

        # Remove both matching models
        channel.data_objects.remove(file_data_object)
        self.assertEqual(channel.data_objects.count(), 0)
