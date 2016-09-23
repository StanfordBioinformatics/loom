from django.test import TestCase
from analysis.models.data_objects import *
from analysis.serializers.data_objects import *
from analysis.test import fixtures


"""This module tests the core functionality in 
analysis.models.base
"""

class TestBaseModel(TestCase):

    def testPolymorphicChildAccessFromParent(self):

        # Setup - Create a model with a polymorphic relationship to child.
        # Reload it from the database
        u = UnnamedFileContent(**fixtures.data_objects.unnamed_file_content)
        u.save()
        content = FileContent(unnamed_file_content=u, filename='x')
        content.save()
        location = FileLocation(**fixtures.data_objects.file_location)
        location.save()
        model = FileDataObject(file_content=content, file_location=location)
        model.save()

        model_reloaded = FileDataObject.objects.get(pk=model.pk)

        # Make sure accessor for child returns subclass, not base class
        self.assertEqual(model_reloaded.file_location.__class__.__name__, 'FileLocation')
        self.assertEqual(model_reloaded.file_location.url, fixtures.data_objects.file_location['url'])
