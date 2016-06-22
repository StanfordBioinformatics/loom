from django.utils import timezone
import json
import os
import uuid

from analysis import get_setting
from analysis.models.base import AnalysisAppInstanceModel, \
    AnalysisAppImmutableModel
from universalmodels import fields


class DataObject(AnalysisAppInstanceModel):
    """A reference to DataObjectContent. While there is only one
    object for each set of content, there can be many references
    to it. That way if the same content arises twice independently 
    we can still keep separate provenance graphs.
    """

    TYPE_CHOICES = (
        ('file', 'File'),
        ('boolean', 'Boolean'),
        ('string', 'String'),
        ('integer', 'Integer'),
        ('json', 'JSON'),
        # ('file_array', 'File Array'),
        # ('boolean_array', 'Boolean Array'),
        # ('string_array', 'String Array'),
        # ('integer_array', 'Integer Array'),
        # ('float', 'Float'),
        # ('float_array', 'Float Array'),
        # ('json_array', 'JSON Array')
    )

    def get_type(self):
        return self.downcast().TYPE

    def get_content(self):
        return self.downcast().get_content()

    def is_ready(self):
        return self.downcast().is_ready()

    @classmethod
    def get_by_value(cls, value, type):
        return class_type_map[type].get_by_value(value)


class DataObjectContent(AnalysisAppImmutableModel):
    """A unit of data passed into or created by analysis steps.
    This may be a file, an array of files, a JSON data object, 
    or an array of JSON objects.
    """

    def get_substitution_value(self):
        return self.downcast().get_substitution_value()


class FileDataObject(DataObject):

    NAME_FIELD = 'file_content__filename'

    TYPE = 'file'

    file_content = fields.ForeignKey('FileContent', null=True)
    file_import = fields.OneToOneField('AbstractFileImport', related_name='data_object')

    def get_content(self):
        return self.file_content

    @classmethod
    def get_by_value(cls, value):
        file_data_objects = cls.get_by_name_and_full_id(value)
        assert len(file_data_objects) == 1
        return file_data_objects.first()

    def get_substitution_value(self):
        return self.file_content.get_substitution_value()

    def after_create_or_update(self, data):
        # A FileLocation should be generated once file_content is set
        if self.file_content and not self.file_import.file_location:
            # If a file with identical content has already been uploaded, re-use
            # it if permitted by settings.
            if self.file_content.has_location() and not get_setting('KEEP_DUPLICATE_FILES'):
                self.file_import.set_location(self.file_content.get_location())
            else:
                self.file_import.create_location()

    def is_ready(self):
        if self.file_import.file_location:
            return self.file_import.file_location.status == 'complete'
        else:
            return False


class FileContent(DataObjectContent):
    """Represents a file, including its content (identified by a hash), its 
    file name, and user-defined metadata.
    """

    filename = fields.CharField(max_length=255)
    unnamed_file_content = fields.ForeignKey('UnnamedFileContent')

    def get_substitution_value(self):
        return self.filename

    def has_location(self):
        return self.unnamed_file_content.file_locations.count() > 0

    def get_location(self):
        location_count = self.unnamed_file_content.file_locations.count()
        assert location_count == 1, "Expected 1 location but found %s for file %s" % (location_count, self.filename)
        return self.unnamed_file_content.file_locations.first()


class UnnamedFileContent(AnalysisAppImmutableModel):
    """Represents file content, identified by a hash. Ignores file name.
    """

    hash_value = fields.CharField(max_length=100)
    hash_function = fields.CharField(max_length=100)


class FileLocation(AnalysisAppInstanceModel):
    """Location of file content.
    """

    unnamed_file_content = fields.ForeignKey(
        'UnnamedFileContent',
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
    def get_location_for_import(cls, file_import):
        return cls.create({
            'url': cls._get_url(cls._get_path_for_import(file_import)),
            'unnamed_file_content': file_import.data_object.file_content.unnamed_file_content
        })

    @classmethod
    def _get_path_for_import(cls, file_import):
        if get_setting('KEEP_DUPLICATE_FILES') and get_setting('FORCE_RERUN'):
            # If both are True, we can organize the directory structure in
            # a human browsable way
            return os.path.join(
                '/',
                get_setting('FILE_ROOT'),
                file_import.get_browsable_path(),
                "%s-%s-%s" % (
                    timezone.now().strftime('%Y%m%d%H%M%S'),
                    file_import.data_object._id,
                    file_import.data_object.file_content.filename
                )
            )
        elif get_setting('KEEP_DUPLICATE_FILES'):
            # Use a flat directory structure but give files with identical content distinctive names
            return os.path.join(
                '/',
                get_setting('FILE_ROOT'),
                '%s-%s-%s' % (
                    timezone.now().strftime('%Y%m%d%H%M%S'),
                    file_import.data_object._id,
                    file_import.data_object.file_content.filename
                )
            )
        else:
            # Use a flat directory structure and use file names that reflect content
            return os.path.join(
                '/',
                get_setting('FILE_ROOT'),
                '%s-%s' % (
                    file_import.data_object.file_content.unnamed_file_content.hash_function,
                    file_import.data_object.file_content.unnamed_file_content.hash_value
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
            get_setting('FILE_ROOT'),
            'tmp',
            uuid.uuid4().hex
        )

    @classmethod
    def _get_url(cls, path):
        FILE_SERVER_TYPE = get_setting('FILE_SERVER_TYPE')
        if FILE_SERVER_TYPE == 'LOCAL':
            return 'file://' + path
        elif FILE_SERVER_TYPE == 'GOOGLE_CLOUD':
            if 'BUCKET_ID' == '':
                raise Exception('Bucket ID is not set.')
            return 'gs://' + os.path.join(get_setting('BUCKET_ID'), path)
        else:
            raise Exception('Couldn\'t recognize value for setting FILE_SERVER_TYPE="%s"' % FILE_SERVER_TYPE)


class AbstractFileImport(AnalysisAppInstanceModel):

    temp_file_location = fields.OneToOneField('FileLocation', null=True, related_name='temp_file_import')
    file_location = fields.ForeignKey('FileLocation', null=True, related_name='file_imports')

    def after_create_or_update(self, data):
        # If there is no FileLocation, set a temporary one.
        # The client will need this to know upload destination, but we
        # can't create a permanent FileLocation until we know the file hash, since
        # it may be used in the name of the file location.
        if not self.temp_file_location and not self.file_location:
            self._set_temp_file_location()

    def _set_temp_file_location(self):
        """A temp location is used since the hash is used in the final file location,
        and this may not be known at time of upload. This is because the method for 
        copying the file also may also generate the hash.
        """
        self.update({'temp_file_location': FileLocation.get_temp_location()})

    def set_location(self, file_location):
        self.update({'file_location': file_location})

    def create_location(self):
        """After uploading the file to a temp location and updating the FileImport with the full 
        FileDataObject (which includes the hash), the final storage location can be determined.
        """
        self.set_location(FileLocation.get_location_for_import(self))


class FileImport(AbstractFileImport):

    note = fields.TextField(max_length=10000, null=True)
    source_url = fields.TextField(max_length=1000)

    def get_browsable_path(self):
        return 'imported'

class DatabaseDataObject(DataObject):

    def is_ready(self):
        # Always ready if it exists in the database
        return True

    class Meta:
        abstract = True


class JSONDataObject(DatabaseDataObject):

    TYPE = 'json'

    json_content = fields.ForeignKey('JSONDataContent')

    def get_content(self):
        return self.json_content

    @classmethod
    def get_by_value(cls, value):
        return cls.create(
            {
                'json_content': {
                    'json_value': json.loads(value)
                }
            }
        )


class JSONDataContent(DataObjectContent):

    json_value = fields.JSONField()

    def get_substitution_value(self):
        return self.json_value


class StringDataObject(DatabaseDataObject):
    
    TYPE = 'string'
    
    string_content = fields.ForeignKey('StringDataContent')

    def get_content(self):
        return self.string_content

    @classmethod
    def get_by_value(cls, value):
        return cls.create(
            {
                'string_content': {
                    'string_value': value
                }
            }
        )


class StringDataContent(DataObjectContent):

    string_value = fields.TextField()

    def get_substitution_value(self):
        return self.string_value


class BooleanDataObject(DatabaseDataObject):
    
    TYPE = 'boolean'
    
    boolean_content = fields.ForeignKey('BooleanDataContent')

    def get_content(self):
        return self.boolean_content

    @classmethod
    def get_by_value(cls, value):
        if value == 'true':
            b = True
        elif value == 'false':
            b = False
        else:
            raise Exception('Could not parse boolean value "%s". Use "true" or "false".' % value)
        return cls.create(
            {
                'boolean_content': {
                    'boolean_value': b
                }
            }
        )


class BooleanDataContent(DataObjectContent):

    boolean_value = fields.BooleanField()

    def get_substitution_value(self):
        return self.boolean_value


class IntegerDataObject(DatabaseDataObject):
    
    TYPE = 'integer'
    
    integer_content = fields.ForeignKey('IntegerDataContent')

    def get_content(self):
        return self.integer_content

    @classmethod
    def get_by_value(cls, value):
        return cls.create(
            {
                'integer_content': {
                    'integer_value': int(value)
                }
            }
        )


class IntegerDataContent(DataObjectContent):

    integer_value = fields.IntegerField()

    def get_substitution_value(self):
        return self.integer_value


class_type_map = {
    'file': FileDataObject,
    'boolean': BooleanDataObject,
    'string': StringDataObject,
    'integer': IntegerDataObject,
    'json': JSONDataObject,
}


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
