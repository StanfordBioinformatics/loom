from django.db import models
import jsonfield
from immutable.models import ImmutableModel, MutableModel
from xppf.common.exceptions import AbstractMethodException
from .common import AnalysisAppBaseModel


class DataObject(ImmutableModel, AnalysisAppBaseModel):

    _class_name = ('data_object', 'data_objects')

    def get_data_object(self):
        # For use as a source, which may be a DataObject or a StepRunPort
        return self


class File(DataObject):

    _class_name = ('file', 'files')

    FOREIGN_KEY_CHILDREN = ['file_contents']
    JSON_FIELDS = ['metadata']

    metadata = jsonfield.JSONField(null=True)
    file_contents = models.ForeignKey('FileContents')

    def is_available(self):
        return self.file_contents.has_storage_location()

    def render_as_list(self):
        return [self]


class FileContents(ImmutableModel, AnalysisAppBaseModel):

    _class_name = ('file_contents', 'file_contents')

    hash_value = models.CharField(max_length = 100)
    hash_function = models.CharField(max_length = 100)

    def has_storage_location(self):
        return self.filestoragelocation_set.exists()


class FileStorageLocation(MutableModel, AnalysisAppBaseModel):

    _class_name = ('file_storage_location', 'file_storage_locations')

    FOREIGN_KEY_CHILDREN = ['file_contents']

    file_contents = models.ForeignKey('FileContents', null=True)

    @classmethod
    def get_by_file(self, file):
        return self.objects.filter(file_contents=file.file_contents).all()


class ServerFileStorageLocation(FileStorageLocation):

    _class_name = ('file_server_location', 'file_server_locations')

    host_url = models.CharField(max_length = 256)
    file_path = models.CharField(max_length = 256)


class FileArray(DataObject):

    _class_name = ('file_array', 'file_arrays')
    
    files = models.ManyToManyField(File)

    def is_available(self):
        return all([file.is_available() for file in self.files.all()])
    
    def render_as_list(self):
        return [file for file in self.files.all()]
