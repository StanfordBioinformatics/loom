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


"""
# Draft work for handling file import requests, where a workflow is defined with inputs
# that have not yet been uploaded.

class FileImportRequest(MutableModel, AnalysisAppBaseModel):
    _class_name = ('file_import_request', 'file_import_requests')
    FOREIGN_KEY_CHILDREN = ['file_storage_location']

    file_storage_location = models.ForeignKey('FileStorageLocation')
    comments = models.CharField(max_length = 10000)
    requester = models.CharField(max_length = 100)

    def is_file_available(self):
        if self.file_storage_location.file is None:
            return False
        return self.file_storage_location.file.is_available()

    def get_file(self):
        return self.file_storage_location.file

    def register_file(self, file):
        self.file_storage_location.file = File.create(file)
        self.save()

class FileHandle(MutableModel, AnalysisAppBaseModel):
    _class_name = ('file_handle', 'file_handles')

    def is_available(self):
        raise AbstractMethodException

    def get_file(self):
        raise AbstractMethodException

class FileInstanceHandle():
    _class_name = ('file_instance_handle', 'file_instance_handles')
    file = models.ForeignKey('File', null=True)

    def is_available(self):
        # return file.exists and is_available
        pass

    def get_file(self):
        # return file
        pass

class FileImportRequestHandle():
    _class_name = ('file_import_request_handle', 'file_import_request_handles')
    file_import_request = models.ForeignKey('FileImportRequest', null=True)

    def is_available(self):
        # return file_storage_location.file.exists and is_available
        pass

    def get_file(self):
        # return file_storage_location.file
        pass
"""
