from django.test import TestCase
from api.models.data_objects import *
from api import exceptions


class TestBase(TestCase):

    def testConcurrentUpdate(self):
        file_data_object = FileDataObject.objects.create(
            type='file',
            filename='myfile.dat',
            source_type='imported',
            file_import={'source_url': 'file:///data/myfile.dat',
                         'note': 'Test data'},
            md5='abcde'
        )

        file_id = file_data_object.id

        file1 = FileDataObject.objects.get(id=file_id)
        file2 = FileDataObject.objects.get(id=file_id)

        file1.filename = 'one'
        file2.flename = 'two'

        file1.save()
        with self.assertRaises(exceptions.ConcurrentModificationError):
            file2.save()
