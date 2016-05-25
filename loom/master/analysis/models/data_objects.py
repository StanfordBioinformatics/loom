from django.conf import settings
from django.utils import timezone
import os

from analysis.exceptions import DataObjectValidationError
from analysis.models.base import AnalysisAppInstanceModel, \
    AnalysisAppImmutableModel
from universalmodels import fields


class DataObject(AnalysisAppImmutableModel):
    """A unit of data passed into or created by analysis steps.
    This may be a file, an array of files, a JSON data object, 
    or an array of JSON objects.
    """
    pass


class FileImport(AnalysisAppInstanceModel):
    file_data_object = fields.ForeignKey(
        'FileDataObject',
        related_name = 'file_import')
    note = fields.TextField(max_length=10000, null=True)
    source_url = fields.TextField(max_length=1000)
    file_storage_location = fields.ForeignKey('FileStorageLocation', null=True)

    @classmethod
    def create(cls, data):
        o = super(FileImport, cls).create(data)
        o._set_file_storage_location()
        return o

    def _set_file_storage_location(self):
        self.file_storage_location = FileStorageLocation.get_location_for_import(self.file_data_object.filename, self.file_data_object._id)
        self.save()

'''    
class DataObjectArray(DataObject):
    """An array of data objects, all of the same type.
    """
    data_objects = fields.ManyToManyField('DataObject',
                                          related_name = 'parent')

    @classmethod
    def create(cls, data):
        o = super(DataObjectArray, cls).create(data)
        cls._verify_children_have_same_type(o)
        return o

    def _verify_children_have_same_type(self):
        child_classes = set()
        for data_object in self.data_objects.all():
            child_classes.add(data_object.downcast().__class__)
            if len(child_classes) > 1:
                raise DataObjectValidationError()
    
    def is_available(self):
        """An array is available if all members are available"""
        return all([member.downcast().is_available() for member in
                    self.data_objects.all()])
'''


class FileDataObject(DataObject):
    """Represents a file, including its contents (identified by a hash), its 
    file name, and user-defined metadata.
    """

    NAME_FIELD = 'filename'

    filename = fields.CharField(max_length=255)
    file_contents = fields.ForeignKey('FileContents')
    metadata = fields.JSONField()

    def is_available(self):
        """A file is available if we can find any storage location for the file 
        contents
        """
        return self.file_contents.has_storage_location()


class FileContents(AnalysisAppImmutableModel):
    """Represents file contents, identified by a hash. Ignores file name.
    """

    hash_value = fields.CharField(max_length=100)
    hash_function = fields.CharField(max_length=100)

    def has_storage_location(self):
        return self.file_storage_locations.exists()


class FileStorageLocation(AnalysisAppInstanceModel):
    """Base class for any type of location where a specified set 
    of file contents can be found.
    """

    file_contents = fields.ForeignKey(
        'FileContents', null=True, related_name='file_storage_locations')
    url = fields.CharField(max_length=1000)
    status = fields.CharField(
        max_length=256,
        default='incomplete',
        choices=(('incomplete', 'Incomplete'),
                 ('complete', 'Complete'),
                 ('failed', 'Failed'))
    )

    @classmethod
    def get_by_file(self, file):
        locations = self.objects.filter(file_contents=file.file_contents).all()
        return locations

    @classmethod
    def get_location_for_import(cls, filename, file_id):
        return cls.create({
            'url': cls._get_url_for_import(filename, file_id)
        })

    @classmethod
    def _get_url_for_import(cls, filename, file_id):
        if settings.FILE_SERVER_TYPE == 'LOCAL':
            return 'file://' + cls._get_path_for_import(filename, file_id)
        elif settings.FILE_SERVER_TYPE == 'GOOGLE_CLOUD':
            return 'gs://' + os.path.join(settings.BUCKET_ID, cls._get_path_for_import(filename, file_id))
        else:
            raise Exception('Couldn\'t recognize value for setting FILE_SERVER_TYPE="%s"' % settings.FILE_SERVER_TYPE)

    @classmethod
    def _get_path_for_import(cls, filename, file_id):
        return os.path.join(
            '/',
            settings.FILE_ROOT,
            settings.IMPORT_DIR,
            "%s-%s-%s" % (
                timezone.now().strftime('%Y%m%d%H%M%S'),
                file_id[0:10],
                filename
            )
        )

'''
class DatabaseDataObject(DataObject):

    def is_available(self):
        """An object stored in the database is always available.
        """
        return True

    class Meta:
        abstract = True


class JSONDataObject(DatabaseDataObject):
    """Contains any valid JSON value. This could be 
    an integer, string, float, boolean, list, or dict
    """

    json_data = fields.JSONField()


class StringDataObject(DatabaseDataObject):

    string_value = fields.TextField()


class BooleanDataObject(DatabaseDataObject):

    boolean_value = fields.BooleanField()


class IntegerDataObject(DatabaseDataObject):

    integer_value = fields.IntegerField()
'''
