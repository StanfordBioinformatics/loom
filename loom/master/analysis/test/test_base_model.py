from django.test import TestCase
from analysis.models.data_objects import *
from analysis.models.channels import *
from analysis.serializers.data_objects import *
from analysis.serializers.channels import *
from . import fixtures


"""This module tests the core functionality in 
analysis.models.base and analysis.serializers.base

Rather than maintain a suite of test models, we use real 
models, selected because they that extend our base model 
classes and exhibit polymorphic inheritance and nested 
structure with various relationship types. But the tests 
are targeting the behavior of the base classes, and model 
tests belong elsewhere.
"""

class TestBaseModel(TestCase):

    def testDeserializerCreateNestedPolymorphic(self):

        # Setup - Create a model with a polymorphic relationship to child
        s = FileDataObjectSerializer(data=fixtures.data_objects.file_data_object)
        s.is_valid()
        file_data_object = s.save()

        # file_data_object.file_import is polymorphic. Make sure we created the
        # model with the FileImport subclass (not the AbstractFileImport base class)
        # and have access to its fields.
        self.assertEqual(file_data_object.file_import.__class__.__name__, 'FileImport')
        self.assertEqual(file_data_object.file_import.note, fixtures.data_objects.file_data_object['file_import']['note'])

    def testPolymorphicChildAccessFromParent(self):

        # Setup - Create a model with a polymorphic relationship to child.
        # Reload it from the database
        s = FileDataObjectSerializer(data=fixtures.data_objects.file_data_object)
        s.is_valid()
        file_data_object = s.save()
        reloaded = FileDataObject.objects.get(id=file_data_object.id)

        # Make sure accessor for child returns subclass, not base class
        self.assertEqual(reloaded.file_import.__class__.__name__, 'FileImport')
        self.assertEqual(reloaded.file_import.note, fixtures.data_objects.file_data_object['file_import']['note'])

    def testDeserializerUpdateCharField(self):

        # Setup - create a model with CharField
        s = FileContentSerializer(data=fixtures.data_objects.file_content)
        s.is_valid()
        file_content = s.save()
        file_content_id = file_content.id

        # Update char field on existing model
        new_filename = 'new_filename'
        data = {
            'filename': new_filename
        }
        s = FileContentSerializer(file_content, data=data, partial=True)
        s.is_valid()
        s.save()

        # Load from DB and verify that the field was updated
        self.assertEqual(FileContent.objects.get(id=file_content_id).filename, new_filename)

    def testDeserializerCreateForeignKeyChild(self):

        # Setup - create a model with ForeignKey field unassigned
        s = FileDataObjectSerializer(data={'file_import': fixtures.data_objects.file_import})
        s.is_valid()
        file_data_object = s.save()

        # Create child related by foreign key
        data = {'file_content': fixtures.data_objects.file_content}
        s = FileDataObjectSerializer(file_data_object, data=data, partial=True)
        s.is_valid()
        new_file_content = s.save()

        # Load from DB and verify that child  was created
        file_data_object = FileDataObject.objects.get(id=file_data_object.id)

        self.assertEqual(file_data_object.file_content.unnamed_file_content.hash_value, fixtures.data_objects.file_content['unnamed_file_content']['hash_value'])

    def testDeserializerUpdateForeignKeyChild(self):

        # Setup - create a model with ForeignKey
        s = FileContentSerializer(data=fixtures.data_objects.file_content)
        s.is_valid()
        file_content = s.save()
        file_content_id = file_content.id
        unnamed_file_content_id = file_content.unnamed_file_content.id

        # Update child model related by foreignkey
        new_hash_value = 'new_hash'
        data = s.data
        data['unnamed_file_content']['hash_value'] = new_hash_value
        
        s = FileContentSerializer(file_content, data=data, partial=True)
        s.is_valid()
        new_file_content = s.save()

        # Load from DB and verify that child  was updated
        unnamed_file_content = FileContent.objects.get(id=file_content_id).unnamed_file_content

        # Field value was set
        self.assertEqual(unnamed_file_content.hash_value, new_hash_value)
        # Primary key was not changed by update
        self.assertEqual(unnamed_file_content.id, unnamed_file_content_id)

    def testDeserializerCreateOneToOneChild(self):

        # Setup - create a model with OneToOne field unassigned
        s = FileImportSerializer(data={'note': 'note text', 'source_url': 'file:///somewhere'})
        s.is_valid()
        file_import = s.save()

        # Create child related by OneToOne
        data = {'file_location': fixtures.data_objects.file_location}
        s = FileImportSerializer(file_import, data=data, partial=True)
        s.is_valid()
        new_file_import = s.save()

        # Load from DB and verify that child  was created
        file_import = FileImport.objects.get(id=file_import.id)

        self.assertEqual(file_import.file_location.url, fixtures.data_objects.file_location['url'])

    def testDeserializerUpdateOneToOneChild(self):

        # Setup - create a model with OneToOne field unassigned
        s = FileImportSerializer(data={
            'note': 'note text',
            'source_url': 'file:///somewhere',
            'file_location': fixtures.data_objects.file_location
        })
        s.is_valid()
        file_import = s.save()
        file_import_id = file_import.id
        file_location_id = file_import.file_location.id
        
        # Update child related by OneToOne
        new_url = 'some://url'
        data = s.data
        data['file_location']['url'] = new_url
        
        s = FileImportSerializer(file_import, data=data, partial=True)
        s.is_valid()
        new_file_import = s.save()

        # Load from DB and verify that child  was updated
        file_location = FileImport.objects.get(id=file_import_id).file_location

        # Field value was set
        self.assertEqual(file_location.url, new_url)
        # Primary key was not changed by update
        self.assertEqual(file_location.id, file_location_id)

    def testManyToManyAddDuplicate(self):

        # Setup - create parent and child models
        s = FileDataObjectSerializer(data=fixtures.data_objects.file_data_object)
        s.is_valid()
        file_data_object = s.save()
        
        channel = Channel(name='channelx')
        channel.save()

        # Add same child instance twice
        channel.data_objects.add(file_data_object)
        channel.data_objects.add(file_data_object)

        # Were both relationships recorded?
        self.assertEqual(channel.data_objects.count(), 2)

    def testManyToManyPreserveOrder(self):

        # Setup - create parent and child models
        s1 = FileDataObjectSerializer(data=fixtures.data_objects.file_data_object)
        s1.is_valid()
        f1 = s1.save()

        s2 = FileDataObjectSerializer(data=fixtures.data_objects.file_data_object)
        s2.is_valid()
        f2 = s2.save()
        
        s3 = FileDataObjectSerializer(data=fixtures.data_objects.file_data_object)
        s3.is_valid()
        f3 = s3.save()

        channel = Channel(name='channelx')
        channel.save()

        # Create M2M relationship, add models in an order that differs from order of creation
        channel.data_objects.add(f1)
        channel.data_objects.add(f3)
        channel.data_objects.add(f2)
        flist = channel.data_objects.all()

        # Verify that queryset order corresponds to order of adding, not creating
        self.assertEqual(flist[0].id, f1.id)
        self.assertEqual(flist[1].id, f3.id) # inverted from creation order
        self.assertEqual(flist[2].id, f2.id) # inverted from creation order

    def testRemoveDuplicateFromManyToMany(self):

        # Since we altered the ManyToMany class to make it accept duplicates,
        # the "remove" function should remove all instances of a given model
        
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

    def testDeserializerCreateManyToManyChildren(self):

        # Create model with M2M related children
        channel_data = {
            'name': 'channelx',
            'data_objects': [
                fixtures.data_objects.file_data_object,
                fixtures.data_objects.file_data_object_2
            ]
        }
        
        s = ChannelSerializer(data=channel_data)
        s.is_valid()
        channel = s.save()

        # Verify children count, order, and content
        self.assertEqual(channel.data_objects.count(), 2)
        self.assertEqual(channel.data_objects.first().file_content.filename, fixtures.data_objects.file_data_object['file_content']['filename'])
        self.assertEqual(channel.data_objects.last().file_content.filename, fixtures.data_objects.file_data_object_2['file_content']['filename'])

    def testDeserializerUpdateManyToManyChildren(self):

        # Create model with M2M related children
        channel_data = {
            'name': 'channelx',
            'data_objects': [
                fixtures.data_objects.file_data_object,
                fixtures.data_objects.file_data_object_2
            ]
        }
        
        s = ChannelSerializer(data=channel_data)
        s.is_valid()
        channel = s.save()

        # Perform update. Replace existing list with nothing.
        channel_data = s.data
        channel_data['data_objects'] = []

        s = ChannelSerializer(data=channel_data, partial=True)
        s.is_valid()
        channel = s.save()

        # Verify all children were dropped
        self.assertEqual(channel.data_objects.count(), 0)

        # Perform update. Add new children

        channel_data = s.data
        channel_data['data_objects'] = [
            fixtures.data_objects.file_data_object_2,
            fixtures.data_objects.file_data_object,
        ]

        s = ChannelSerializer(data=channel_data)
        s.is_valid()
        channel = s.save()
        
        # Verify children count, order, and content
        self.assertEqual(channel.data_objects.count(), 2)
        self.assertEqual(channel.data_objects.first().file_content.filename, fixtures.data_objects.file_data_object_2['file_content']['filename'])
        self.assertEqual(channel.data_objects.last().file_content.filename, fixtures.data_objects.file_data_object['file_content']['filename'])

        # Perform update. Ignore children
        channel_data = s.data
        s = ChannelSerializer(data=channel_data)
        s.is_valid()
        channel = s.save()

        # Verify children are unchanged
        self.assertEqual(channel.data_objects.count(), 2)
        self.assertEqual(channel.data_objects.first().file_content.filename, fixtures.data_objects.file_data_object_2['file_content']['filename'])
        self.assertEqual(channel.data_objects.last().file_content.filename, fixtures.data_objects.file_data_object['file_content']['filename'])

    def testDeserializerCreateOneToManyChildren(self):

        # Create model with One2M children
        channel_data = {
            'name': 'channelx',
            'outputs': [
                {
                    'data_objects': [
                        fixtures.data_objects.file_data_object,
                    ]
                },
                {
                    'data_objects': [
                        fixtures.data_objects.file_data_object_2,
                    ]
                }
            ]
        }
        
        s = ChannelSerializer(data=channel_data)
        s.is_valid()
        channel = s.save()

        # Verify children count, order, and content
        self.assertEqual(channel.outputs.count(), 2)
        self.assertEqual(channel.outputs.first().data_objects.first().file_content.filename,
                         fixtures.data_objects.file_data_object['file_content']['filename'])
        self.assertEqual(channel.outputs.last().data_objects.first().file_content.filename,
                         fixtures.data_objects.file_data_object_2['file_content']['filename'])

    def testDeserializerUpdateOneToManyChildren(self):

        # Create model with One2M children
        channel_data = {
            'name': 'channelx',
            'outputs': [
                {
                    'data_objects': [
                        fixtures.data_objects.file_data_object,
                    ]
                },
                {
                    'data_objects': [
                        fixtures.data_objects.file_data_object_2,
                    ]
                }
            ]
        }
        
        s = ChannelSerializer(data=channel_data)
        s.is_valid()
        channel = s.save()

        
        # Verify children count, order, and content
        self.assertEqual(channel.outputs.count(), 2)
        self.assertEqual(channel.outputs.first().data_objects.first().file_content.filename,
                         fixtures.data_objects.file_data_object['file_content']['filename'])
        self.assertEqual(channel.outputs.last().data_objects.first().file_content.filename,
                         fixtures.data_objects.file_data_object_2['file_content']['filename'])

