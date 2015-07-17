from django.db import models

from .common import AnalysisAppBaseModel
from immutable.models import ImmutableModel, MutableModel


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
    file = models.ForeignKey(File, null=True)

    @classmethod
    def get_by_file(self, file):
        return self.objects.filter(file=file).all()

class FilePathLocation(FileLocation):
    _class_name = ('file_path_location', 'file_path_locations')

    file_path = models.CharField(max_length = 256)

class FileImportRequest(MutableModel, AnalysisAppBaseModel):
    _class_name = ('file_import_request', 'file_import_requests')
    FOREIGN_KEY_CHILDREN = ['file_location']
    import_comments = models.CharField(max_length = 10000)
    file_location = models.ForeignKey('FileLocation')
    requester = models.CharField(max_length = 100)
