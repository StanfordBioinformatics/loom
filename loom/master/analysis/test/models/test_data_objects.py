import copy
from django.test import TestCase
from django.db import IntegrityError
from django.db.models import ProtectedError

from analysis.models.data_objects import *
from analysis.test import fixtures


class TestDataObject(TestCase):

    def testCreateAsSubclass(self):
        content = BooleanContent(**fixtures.data_objects.boolean_content)
        content.save()
        boolean_data_object = copy.deepcopy(fixtures.data_objects.boolean_data_object)
        boolean_data_object['boolean_content'] = content
        do = BooleanDataObject(**boolean_data_object)
        do.save()
        self.assertEqual(DataObject.objects.count(), 1)


class TestDataObjectContent(TestCase):

    def testCreateAsSubclass(self):
        content = StringContent(**fixtures.data_objects.string_content)
        content.save()
        self.assertEqual(DataObjectContent.objects.count(), 1)
        self.assertEqual(StringContent.objects.count(), 1)

    def testDeleteAsSubclass(self):
        content = StringContent(**fixtures.data_objects.string_content)
        content.save()
        content.delete()
        self.assertEqual(DataObjectContent.objects.count(), 0)
        self.assertEqual(StringContent.objects.count(), 0)

    def testDeleteAsSuperclass(self):
        content = StringContent(**fixtures.data_objects.string_content)
        content.save()
        DataObjectContent.objects.first().delete()
        self.assertEqual(DataObjectContent.objects.count(), 0)
        self.assertEqual(StringContent.objects.count(), 0)


class TestFileDataObject(TestCase):

    def testCreate(self):
        u = UnnamedFileContent(**fixtures.data_objects.unnamed_file_content)
        u.save()
        content = FileContent(unnamed_file_content=u, filename='x')
        content.save()
        location = FileLocation(**fixtures.data_objects.file_location)
        location.save()
        do = FileDataObject(file_content=content, file_location=location)
        do.save()
        self.assertEqual(FileDataObject.objects.count(), 1)

    def testDelete(self):
        u = UnnamedFileContent(**fixtures.data_objects.unnamed_file_content)
        u.save()
        content = FileContent(unnamed_file_content=u, filename='x')
        content.save()
        location = FileLocation(**fixtures.data_objects.file_location)
        location.save()
        do = FileDataObject(file_content=content, file_location=location)
        do.save()
        self.assertEqual(FileDataObject.objects.count(), 1)

        do.delete()
        self.assertEqual(FileDataObject.objects.count(), 0)
        self.assertEqual(FileLocation.objects.count(), 1) # Should not be removed until disk space is freed.
        self.assertEqual(FileContent.objects.count(), 0)


class TestFileContent(TestCase):
    
    def testCreate(self):
        u = UnnamedFileContent(**fixtures.data_objects.unnamed_file_content)
        u.save()
        content = FileContent(unnamed_file_content=u, filename='x')
        content.save()
        self.assertEqual(FileContent.objects.count(), 1)

    def testDelete(self):
        u = UnnamedFileContent(**fixtures.data_objects.unnamed_file_content)
        u.save()
        content = FileContent(unnamed_file_content=u, filename='x')
        content.save()
        self.assertEqual(FileContent.objects.count(), 1)
        self.assertEqual(UnnamedFileContent.objects.count(), 1)
        content.delete()
        self.assertEqual(FileContent.objects.count(), 0)
        self.assertEqual(UnnamedFileContent.objects.count(), 0)


class TestUnnamedFileContent(TestCase):
    
    def testCreate(self):
        u = UnnamedFileContent(**fixtures.data_objects.unnamed_file_content)
        u.save()
        self.assertEqual(UnnamedFileContent.objects.count(), 1)

    def testDelete(self):
        u = UnnamedFileContent(**fixtures.data_objects.unnamed_file_content)
        u.save()
        self.assertEqual(UnnamedFileContent.objects.count(), 1)
        u.delete()
        self.assertEqual(UnnamedFileContent.objects.count(), 0)

    def testDeleteProtected(self):
        u = UnnamedFileContent(**fixtures.data_objects.unnamed_file_content)
        u.save()
        content = FileContent(unnamed_file_content=u, filename='x')
        content.save()
        with self.assertRaises(ProtectedError):
            u.delete()
        
    def testUniqueConstraint(self):
        u = UnnamedFileContent(**fixtures.data_objects.unnamed_file_content)
        u.save()

        # Cannot add another second identical object
        u = UnnamedFileContent(**fixtures.data_objects.unnamed_file_content)
        with self.assertRaises(IntegrityError):
            u.save()
        

class TestFileLocation(TestCase):

    def testCreate(self):
        location = FileLocation(**fixtures.data_objects.file_location)
        location.save()
        self.assertEqual(FileLocation.objects.count(), 1)

    def testDelete(self):
        location = FileLocation(**fixtures.data_objects.file_location)
        location.save()
        self.assertEqual(FileLocation.objects.count(), 1)
        location.delete()
        self.assertEqual(FileLocation.objects.count(), 0)

    def testDeleteProtected(self):
        u = UnnamedFileContent(**fixtures.data_objects.unnamed_file_content)
        u.save()
        content = FileContent(unnamed_file_content=u, filename='x')
        content.save()
        location = FileLocation(**fixtures.data_objects.file_location)
        location.save()
        do = FileDataObject(file_content=content, file_location=location)
        do.save()
        self.assertEqual(FileDataObject.objects.count(), 1)

        with self.assertRaises(ProtectedError):
            location.delete()

class TestFileImport(TestCase):
    
    def testCreate(self):
        u = UnnamedFileContent(**fixtures.data_objects.unnamed_file_content)
        u.save()
        content = FileContent(unnamed_file_content=u, filename='x')
        content.save()
        location = FileLocation(**fixtures.data_objects.file_location)
        location.save()
        do = FileDataObject(file_content=content, file_location=location)
        do.save()
        self.assertEqual(FileDataObject.objects.count(), 1)

        fi = FileImport(file_data_object=do, note='hey', source_url='file:///my/stuff')
        fi.save()
        self.assertEqual(FileImport.objects.count(), 1)

    def testDeleteCascade(self):
        u = UnnamedFileContent(**fixtures.data_objects.unnamed_file_content)
        u.save()
        content = FileContent(unnamed_file_content=u, filename='x')
        content.save()
        location = FileLocation(**fixtures.data_objects.file_location)
        location.save()
        do = FileDataObject(file_content=content, file_location=location)
        do.save()
        self.assertEqual(FileDataObject.objects.count(), 1)

        fi = FileImport(file_data_object=do, note='hey', source_url='file:///my/stuff')
        fi.save()

        # Deleting data object cascades to delete import
        do.delete()
        self.assertEqual(FileImport.objects.count(), 0)

    def testDelete(self):
        u = UnnamedFileContent(**fixtures.data_objects.unnamed_file_content)
        u.save()
        content = FileContent(unnamed_file_content=u, filename='x')
        content.save()
        location = FileLocation(**fixtures.data_objects.file_location)
        location.save()
        do = FileDataObject(file_content=content, file_location=location)
        do.save()
        self.assertEqual(FileDataObject.objects.count(), 1)

        fi = FileImport(file_data_object=do, note='hey', source_url='file:///my/stuff')
        fi.save()

        # Deleting import leaves data object untouched
        fi.delete()
        self.assertEqual(FileImport.objects.count(), 0)
        self.assertEqual(FileDataObject.objects.count(), 1)


class TestStringDataObject(TestCase):

    def testCreate(self):
        content = StringContent(**fixtures.data_objects.string_content)
        content.save()
        string_data_object = copy.deepcopy(fixtures.data_objects.string_data_object)
        string_data_object['string_content'] = content
        do = StringDataObject(**string_data_object)
        do.save()

        self.assertEqual(StringDataObject.objects.count(), 1)
        
    def testDelete(self):
        content = StringContent(**fixtures.data_objects.string_content)
        content.save()
        string_data_object = copy.deepcopy(fixtures.data_objects.string_data_object)
        string_data_object['string_content'] = content
        do = StringDataObject(**string_data_object)
        do.save()

        do.delete()
        self.assertEqual(StringDataObject.objects.count(), 0)
        self.assertEqual(StringContent.objects.count(), 0)


class TestStringContent(TestCase):

    def testCreate(self):
        content = StringContent(**fixtures.data_objects.string_content)
        content.save()
        self.assertEqual(content.string_value, fixtures.data_objects.string_content['string_value'])

    def testDelete(self):
        content = StringContent(**fixtures.data_objects.string_content)
        content.save()
        self.assertEqual(StringContent.objects.count(), 1)
        content.delete()
        self.assertEqual(StringContent.objects.count(), 0)
        
    def testDeleteProtected(self):
        content = StringContent(**fixtures.data_objects.string_content)
        content.save()
        string_data_object = copy.deepcopy(fixtures.data_objects.string_data_object)
        string_data_object['string_content'] = content
        do = StringDataObject(**string_data_object)
        do.save()
        
        self.assertEqual(StringContent.objects.count(), 1)
        with self.assertRaises(ProtectedError):
            content.delete()
        self.assertEqual(StringContent.objects.count(), 1)


class TestBooleanDataObject(TestCase):

    def testCreate(self):
        content = BooleanContent(**fixtures.data_objects.boolean_content)
        content.save()
        boolean_data_object = copy.deepcopy(fixtures.data_objects.boolean_data_object)
        boolean_data_object['boolean_content'] = content
        do = BooleanDataObject(**boolean_data_object)
        do.save()

        self.assertEqual(BooleanDataObject.objects.count(), 1)

    def testDelete(self):
        content = BooleanContent(**fixtures.data_objects.boolean_content)
        content.save()
        boolean_data_object = copy.deepcopy(fixtures.data_objects.boolean_data_object)
        boolean_data_object['boolean_content'] = content
        do = BooleanDataObject(**boolean_data_object)
        do.save()

        do.delete()
        self.assertEqual(BooleanDataObject.objects.count(), 0)
        self.assertEqual(BooleanContent.objects.count(), 0)


class TestBooleanContent(TestCase):

    def testCreate(self):
        content = BooleanContent(**fixtures.data_objects.boolean_content)
        content.save()
        self.assertEqual(content.boolean_value, fixtures.data_objects.boolean_content['boolean_value'])

    def testDelete(self):
        content = BooleanContent(**fixtures.data_objects.boolean_content)
        content.save()
        self.assertEqual(BooleanContent.objects.count(), 1)
        content.delete()
        self.assertEqual(BooleanContent.objects.count(), 0)
        
    def testDeleteProtected(self):
        content = BooleanContent(**fixtures.data_objects.boolean_content)
        content.save()
        boolean_data_object = copy.deepcopy(fixtures.data_objects.boolean_data_object)
        boolean_data_object['boolean_content'] = content
        do = BooleanDataObject(**boolean_data_object)
        do.save()
        
        self.assertEqual(BooleanContent.objects.count(), 1)
        with self.assertRaises(ProtectedError):
            content.delete()
        self.assertEqual(BooleanContent.objects.count(), 1)


class TestIntegerDataObject(TestCase):

    def testCreate(self):
        content = IntegerContent(**fixtures.data_objects.integer_content)
        content.save()
        integer_data_object = copy.deepcopy(fixtures.data_objects.integer_data_object)
        integer_data_object['integer_content'] = content
        do = IntegerDataObject(**integer_data_object)
        do.save()
        self.assertEqual(IntegerDataObject.objects.count(), 1)

    def testDelete(self):
        content = IntegerContent(**fixtures.data_objects.integer_content)
        content.save()
        integer_data_object = copy.deepcopy(fixtures.data_objects.integer_data_object)
        integer_data_object['integer_content'] = content
        do = IntegerDataObject(**integer_data_object)
        do.save()

        do.delete()
        self.assertEqual(IntegerDataObject.objects.count(), 0)
        self.assertEqual(IntegerContent.objects.count(), 0)


class TestIntegerContent(TestCase):

    def testCreate(self):
        content = IntegerContent(**fixtures.data_objects.integer_content)
        content.save()
        self.assertEqual(content.integer_value, fixtures.data_objects.integer_content['integer_value'])

    def testDelete(self):
        content = IntegerContent(**fixtures.data_objects.integer_content)
        content.save()
        self.assertEqual(IntegerContent.objects.count(), 1)
        content.delete()
        self.assertEqual(IntegerContent.objects.count(), 0)
        
    def testDeleteProtected(self):
        content = IntegerContent(**fixtures.data_objects.integer_content)
        content.save()
        integer_data_object = copy.deepcopy(fixtures.data_objects.integer_data_object)
        integer_data_object['integer_content'] = content
        do = IntegerDataObject(**integer_data_object)
        do.save()
        
        self.assertEqual(IntegerContent.objects.count(), 1)
        with self.assertRaises(ProtectedError):
            content.delete()
        self.assertEqual(IntegerContent.objects.count(), 1)
