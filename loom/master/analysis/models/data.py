from django.conf import settings
from django.utils import timezone
import os
import uuid

from analysis.models.base import AnalysisAppInstanceModel, \
    AnalysisAppImmutableModel
from universalmodels import fields


class Data(AnalysisAppInstanceModel):
    """A reference to DataContents. While there is only one
    object for each set of contents, there can be many references
    to it. That way if the same contents arise twice independently 
    we can still keep separate provenance graphs.
    """
    pass


class DataContents(AnalysisAppImmutableModel):
    """A unit of data passed into or created by analysis steps.
    This may be a file, an array of files, a JSON data object, 
    or an array of JSON objects.
    """
    pass


class FileData(Data):

    NAME_FIELD = 'named_file_contents__filename'
    
    named_file_contents = fields.ForeignKey('NamedFileContents')
    file_location = fields.ForeignKey('FileLocation', null=True)

    @classmethod
    def get_by_name_and_hash(cls, query_string):
        filename, hash_function, hash_value = cls._parse_name_and_hash(query_string)
        if not filename and hash_function and hash_value:
            return cls.objects.none()
        models = cls.get_by_name(filename)
        models = models.filter(named_file_contents__file_contents__hash_function=hash_function)
        return models.filter(named_file_contents__file_contents__hash_value=hash_value)

    @classmethod
    def _parse_name_and_hash(cls, query_string):
        """Parse query string of the form filename@hash_function$hash_value,
        e.g. file.txt@md5$9a6a9c9074509fbff3a65e819bb7eb7f
        """
        parts = query_string.split('@')
        if len(parts) != 2:
            return None, None, None

        filename = parts[0]
        rest = '@'.join(parts[1:])
        hash_parts = rest.split('$')
        if len(parts) < 1:
            return None, None, None

        hash_function = hash_parts[0]
        hash_value = '$'.join(hash_parts[1:])
        return filename, hash_function, hash_value


class NamedFileContents(DataContents):
    """Represents a file, including its contents (identified by a hash), its 
    file name, and user-defined metadata.
    """

    filename = fields.CharField(max_length=255)
    file_contents = fields.ForeignKey('FileContents')


class FileContents(AnalysisAppImmutableModel):
    """Represents file contents, identified by a hash. Ignores file name.
    """

    hash_value = fields.CharField(max_length=100)
    hash_function = fields.CharField(max_length=100)


class FileLocation(AnalysisAppInstanceModel):
    """Location of a set of file contents.
    """

    file_contents = fields.ForeignKey(
        'FileContents',
        null=True,
        related_name='file_locations')
    url = fields.CharField(max_length=1000)
    status = fields.CharField(
        max_length=256,
        default='incomplete',
        choices=(('incomplete', 'Incomplete'),
                 ('complete', 'Complete'),
                 ('failed', 'Failed'))
    )

    @classmethod
    def get_by_file(self, file_data):
        locations = self.objects.filter(file_contents=file_data.named_file_contents.file_contents).all()
        return locations

    @classmethod
    def get_location_for_import(cls, file_data):
        return cls.create({
            'url': cls._get_url(cls._get_path_for_import(file_data)),
            'file_contents': file_data.named_file_contents.file_contents.to_struct()
        })

    @classmethod
    def _get_path_for_import(cls, file_data):
        if not settings.FILE_ROOT:
            raise Exception('FILE_ROOT is not set')

        if settings.BROWSEABLE_FILE_STORAGE:
            if not settings.IMPORT_DIR:
                raise Exception('IMPORT_DIR is not set')
            return os.path.join(
                '/',
                settings.FILE_ROOT,
                settings.IMPORT_DIR,
                "%s-%s-%s" % (
                    timezone.now().strftime('%Y%m%d%H%M%S'),
                    file_data._id,
                    file_data.named_file_contents.filename
                )
            )
        else:
            return os.path.join(
                '/',
                settings.FILE_ROOT,
                '%s-%s' % (
                    file_data.named_file_contents.file_contents.hash_function,
                    file_data.named_file_contents.file_contents.hash_value
                )
            )

    @classmethod
    def get_temp_location(cls,):
        return cls.create({
            'url': cls._get_url(cls._get_temp_path_for_import())
        })

    @classmethod
    def _get_temp_path_for_import(cls):
        return os.path.join(
            '/',
            settings.FILE_ROOT,
            'tmp',
            uuid.uuid4().hex
        )

    @classmethod
    def _get_url(cls, path):
        if settings.FILE_SERVER_TYPE == 'LOCAL':
            return 'file://' + path
        elif settings.FILE_SERVER_TYPE == 'GOOGLE_CLOUD':
            return 'gs://' + os.path.join(settings.BUCKET_ID, path)
        else:
            raise Exception('Couldn\'t recognize value for setting FILE_SERVER_TYPE="%s"' % settings.FILE_SERVER_TYPE)


class FileImport(AnalysisAppInstanceModel):
    file_data = fields.ForeignKey(
        'FileData',
        related_name = 'file_imports',
        null=True)
    note = fields.TextField(max_length=10000, null=True)
    source_url = fields.TextField(max_length=1000)
    temp_file_location = fields.ForeignKey('FileLocation', null=True, related_name='temp_file_import')
    file_location = fields.ForeignKey('FileLocation', null=True)

    def after_create_or_update(self):
        # If there is no FileLocation, set a temporary one.
        # The client will need this to know upload destination, but we
        # can't create a permanent FileLocation until we know the file hash, since
        # it may be used in the name of the file location.
        if not self.temp_file_location and not self.file_location:
            self._set_temp_file_location()

        # If FileData was added and no permanent FileLocation exists,
        # create one. The client will need this to know upload destination.
        elif self.file_data and not self.file_location:
            self._set_file_location()

    def _set_temp_file_location(self):
        """A temp location is used since the hash is used in the final file location,
        and this may not be known at time of upload. This is because the method for 
        copying the file also may also generate the hash.
        """
        self.temp_file_location = FileLocation.get_temp_location()
        self.save()

    def _set_file_location(self):
        """After uploading the file to a temp location and updating the FileImport with the full 
        FileContents (which includes the hash), the final storage location can be determined.
        """
        self.file_location = FileLocation.get_location_for_import(self.file_data)
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
