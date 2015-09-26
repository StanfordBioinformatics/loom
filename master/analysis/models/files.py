from django.db import models

from .common import AnalysisAppBaseModel
from immutable.models import ImmutableModel, MutableModel

from xppf.common.exceptions import AbstractMethodException

class File(ImmutableModel, AnalysisAppBaseModel):
    _class_name = ('file', 'files')

    hash_value = models.CharField(max_length = 100)
    hash_function = models.CharField(max_length = 100)

    def is_available(self):
        return self.filelocation_set.exists()

class FileLocation(MutableModel, AnalysisAppBaseModel):
    # Multitable, not abstract inheritance, so that 
    # pointers to the parent class can be created.

    _class_name = ('file_location', 'file_locations')
    FOREIGN_KEY_CHILDREN = ['file']
    file = models.ForeignKey('File', null=True)

    @classmethod
    def get_by_file(self, file):
        return self.objects.filter(file=file).all()

    def has_file(self):
        return self.file is not None

class FileServerLocation(FileLocation):
    _class_name = ('file_server_location', 'file_server_locations')

    host_url = models.CharField(max_length = 256)
    file_path = models.CharField(max_length = 256)

class FileImportRequest(MutableModel, AnalysisAppBaseModel):
    _class_name = ('file_import_request', 'file_import_requests')
    FOREIGN_KEY_CHILDREN = ['file_location']

    file_location = models.ForeignKey('FileLocation')
    comments = models.CharField(max_length = 10000)
    requester = models.CharField(max_length = 100)

    def is_file_available(self):
        if self.file_location.file is None:
            return False
        return self.file_location.file.is_available()

    def get_file(self):
        return self.file_location.file

    def register_file(self, file):
        self.file_location.file = File.create(file)
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
        # return filelocation.file.exists and is_available
        pass

    def get_file(self):
        # return filelocation.file
        pass
