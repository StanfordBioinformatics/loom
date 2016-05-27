from django.conf import settings
from django.db import transaction
from django.utils import timezone
import json
import os
import uuid

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
        related_name = 'file_imports',
        null=True)
    note = fields.TextField(max_length=10000, null=True)
    source_url = fields.TextField(max_length=1000)
    temp_file_storage_location = fields.ForeignKey('FileStorageLocation', null=True, related_name='temp_file_import')
    file_storage_location = fields.ForeignKey('FileStorageLocation', null=True)

    @classmethod
    def create(cls, data):
        with transaction.atomic():
            o = super(FileImport, cls).create(data)
            o._set_temp_file_storage_location()
        return o

    def update(self, data):
        super(FileImport, self).update(data)

        # If the update adds a FileDataObject, this triggers setting the FileStorageLocation
        data_struct = json.loads(data)
        if data_struct.get('file_data_object') and not data_struct.get('file_storage_location'):
            self._set_file_storage_location()

    def _set_temp_file_storage_location(self):
        """A temp location is used since the FileDataObject ID may be used in the 
        final file location, and this ID may not be known at time of upload. This is
        because the method for copying the file also may also generates the hash
        such that the hash is not known prior to copy. The FileDataObject can't be
        generated before FileContents are known since its ID is a hash of the 
        object's contents.
        """
        self.temp_file_storage_location = FileStorageLocation.get_temp_location()
        self.save()

    def _set_file_storage_location(self):
        """After uploading the file to a temp location and updating the FileImport's FileDataObject with 
        the full FileContents (which includes the hash), the final storage location can be determined.
        """
        self.file_storage_location = FileStorageLocation.get_location_for_import(self.file_data_object)
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
        'FileContents',
        null=True,
        related_name='file_storage_locations')
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
    def get_temp_location(cls,):
        return cls.create({
            'url': cls._get_url(cls._get_temp_path_for_import())
        })

    @classmethod
    def get_location_for_import(cls, file_data_object):
        return cls.create({
            'url': cls._get_url(cls._get_path_for_import(file_data_object.filename, file_data_object._id)),
            'file_contents': file_data_object.file_contents.to_struct()
        })

    @classmethod
    def _get_url(cls, path):
        if settings.FILE_SERVER_TYPE == 'LOCAL':
            return 'file://' + path
        elif settings.FILE_SERVER_TYPE == 'GOOGLE_CLOUD':
            return 'gs://' + os.path.join(settings.BUCKET_ID, path)
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
                file_id[0:12],
                filename
            )
        )

    @classmethod
    def _get_temp_path_for_import(cls):
        return os.path.join(
            '/',
            settings.FILE_ROOT,
            settings.IMPORT_DIR,
            'tmp',
            uuid.uuid4().hex
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
