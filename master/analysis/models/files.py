from django.db import models
import jsonfield

from analysis.models.common import AnalysisAppBaseModel
from immutable.models import ImmutableModel, MutableModel
from loom.common.exceptions import AbstractMethodException


class DataObject(ImmutableModel, AnalysisAppBaseModel):
    """A unit of data passed into or created by analysis steps.
    May be a file or an array of files.
    """

    _class_name = ('data_object', 'data_objects')

    def is_data_object(self):
        return True

    def get_data_object(self):
        """For use as a source, which may be a DataObject or a StepRunPort"""
        return self

    def is_available(self):
        return self.downcast().is_available()

    @property
    def is_array(self):
        return self.downcast().is_array()


class File(DataObject):
    """Represents a file, including its contents (identified by a hash) and
    metadata such as file_name or user-defined metadata.
    """

    _class_name = ('file', 'files')

    FOREIGN_KEY_CHILDREN = ['file_contents']
    JSON_FIELDS = ['metadata']

    metadata = jsonfield.JSONField(null=True)
    file_contents = models.ForeignKey('FileContents')

    def is_array(self):
        return False

    def file_count():
        return 1

    def is_available(self):
        return self.file_contents.has_storage_location()

    def render_as_list(self):
        """For use where DataObject may be an array so result should
        be a list
        """
        return [self]


class FileContents(ImmutableModel, AnalysisAppBaseModel):
    """Represents file contents, identified by a hash. Ignores file name
    or other metadata.
    """

    _class_name = ('file_contents', 'file_contents')

    hash_value = models.CharField(max_length = 100)
    hash_function = models.CharField(max_length = 100)

    def has_storage_location(self):
        return self.filestoragelocation_set.exists()


class FileStorageLocation(MutableModel, AnalysisAppBaseModel):
    """Base class for any type of location where a specified set 
    of file contents can be found.
    """

    _class_name = ('file_storage_location', 'file_storage_locations')

    FOREIGN_KEY_CHILDREN = ['file_contents']

    file_contents = models.ForeignKey('FileContents', null=True)

    @classmethod
    def get_by_file(self, file):
        return self.objects.filter(file_contents=file.file_contents).all()


class ServerFileStorageLocation(FileStorageLocation):
    """File server where a specified set of file contents can be found and 
    accessed by ssh.
    """

    _class_name = ('file_server_location', 'file_server_locations')

    host_url = models.CharField(max_length = 256)
    file_path = models.CharField(max_length = 256)

class GoogleCloudStorageLocation(FileStorageLocation):
    """Project, bucket, and path where a specified set of file contents can be found and 
    accessed using Google Cloud Storage.
    """

    _class_name = ('google_cloud_storage_location', 'google_cloud_storage_locations')

    project_id = models.CharField(max_length = 256)
    bucket_id = models.CharField(max_length = 256)
    blob_path = models.CharField(max_length = 256)

class FileArray(DataObject):
    """Array of files to be treated as a single entity for input/output of analysis
    steps or to be split for parallel workflows.
    """

    _class_name = ('file_array', 'file_arrays')
    
    files = models.ManyToManyField(File)

    def is_array(self):
        return True

    def file_count(self):
        return self.files.count()

    def is_available(self):
        return all([file.is_available() for file in self.files.all()])
    
    def render_as_list(self):
        return [file for file in self.files.all()]
