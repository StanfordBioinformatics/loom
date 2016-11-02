from django.db import models
from django.utils import timezone
from django.dispatch import receiver
import os
import uuid

from .base import BaseModel
from api import get_setting


class TypeMismatchError(Exception):
    pass
class NestedArraysError(Exception):
    pass
class HashNotFoundError(Exception):
    pass
class InvalidFileServerTypeError(Exception):
    pass
class RelativePathError(Exception):
    pass
class RelativeFileRootError(Exception):
    pass
class InvalidSourceTypeError(Exception):
    pass


class DataObjectManager():

    def __init__(self, model):
        self.model = model    


class BooleanDataObjectManager(DataObjectManager):

    @classmethod
    def get_by_value(cls, value):
        return BooleanDataObject.objects.create(value=value, type='boolean')

    def get_substitution_value(self):
        return self.model.booleandataobject.value


class FileDataObjectManager(DataObjectManager):

    @classmethod
    def get_by_value(cls, value):
        # TODO
        pass

    def get_substitution_value(self):
        return self.model.filename


class FloatDataObjectManager(DataObjectManager):

    @classmethod
    def get_by_value(cls, value):
        return FloatDataObject.objects.create(value=value, type='float')

    def get_substitution_value(self):
        return self.model.floatdataobject.value


class IntegerDataObjectManager(DataObjectManager):

    @classmethod
    def get_by_value(cls, value):
        return IntegerDataObject.objects.create(value=value, type='integer')

    def get_substitution_value(self):
        return self.model.integerdataobject.value


class StringDataObjectManager(DataObjectManager):

    @classmethod
    def get_by_value(cls, value):
        return StringDataObject.objects.create(value=value, type='string')

    def get_substitution_value(self):
        return self.model.stringdataobject.value


class DataObjectArrayManager(DataObjectManager):

    def get_substitution_value(self):
        return [member.item.substitution_value
                for member in self.model.array_members.all()]


class DataObject(BaseModel):

    _MANAGER_CLASSES = {
        'boolean': BooleanDataObjectManager,
        'float': FloatDataObjectManager,
        'file': FileDataObjectManager,
        'integer': IntegerDataObjectManager,
        'string': StringDataObjectManager,
    }

    _ARRAY_MANAGER_CLASS = DataObjectArrayManager

    TYPE_CHOICES = (
        ('boolean', 'Boolean'),
        ('file', 'File'),
        ('float', 'Float'),
        ('integer', 'Integer'),
        ('string', 'String'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(
        max_length=255,
        choices=TYPE_CHOICES)
    is_array = models.BooleanField(
        default=False)
    datetime_created = models.DateTimeField(
        default=timezone.now, editable=False)

    @classmethod
    def _get_manager_class(cls, type):
        return cls._MANAGER_CLASSES[type]
        
    def _get_manager(self):
        if self.is_array:
            return self._ARRAY_MANAGER_CLASS(self)
        else:
            return self._get_manager_class(self.type)(self)

    @classmethod
    def get_by_value(cls, value, type):
        return cls._MANAGER_CLASSES[type].get_by_value(value)
 
    @property
    def substitution_value(self):
        return self._get_manager().get_substitution_value()

    def add_to_array(self, array):
        ArrayMembership.objects.create(
            array=array, item=self, order=array.array_members.count())


class BooleanDataObject(DataObject):

    value = models.NullBooleanField()


class FileDataObject(DataObject):

    NAME_FIELD = 'filename'
    HASH_FIELD = 'hashes__value'
    
    filename = models.CharField(max_length=1024)
    file_location = models.ForeignKey('FileLocation', null=True)
    note = models.TextField(max_length=10000, null=True)
    source_url = models.TextField(max_length=1000, null=True)
    source_type = models.CharField(
        max_length=255,
        choices=(('imported', 'Imported'),
                 ('result', 'Result'),
                 ('log', 'Log'))
    )

    def get_hash(self):
        hash = self.hashes.filter(function=get_setting('HASH_FUNCTION')).first()
        if hash is None:
            raise HashNotFoundError(
                'File "%s" does not have a hash of type "%s" defined' % (
                    self.id.hex, get_setting('HASH_FUNCTION')))
        return hash

    def create_location_for_import(self):
        if not self.file_location:
            # Based on settings, choose the path where the
            # file should be stored and create a FileLocation
            # with upload_status=incomplete.
            #
            # If a file with identical content has already been uploaded,
            # re-use it if permitted by settings. Search until we find
            # one match, then continue.
            if not get_setting('KEEP_DUPLICATE_FILES'):
                for hash in self.hashes.all():
                    matching_file_locations = FileLocation.objects.filter(
                        hashes__value=hash.value,
                        hashes__function=hash.function,
                        upload_status='complete')
                    if matching_file_locations.count() > 0:
                        self.file_location = matching_file_locations.first()
                        self.save()
                        return
            # No existing file to use. Create a new location for upload.
            self.file_location \
                = FileLocation.create_location_for_import(self)
            self.save()


class FloatDataObject(DataObject):

    value = models.FloatField(null=True)


class IntegerDataObject(DataObject):

    value = models.IntegerField(null=True)


class StringDataObject(DataObject):

    value = models.TextField(max_length=10000, null=True)


class DataObjectArray(DataObject):

    @classmethod
    def create_from_list(cls, data_object_list, type):
        cls._validate_list(data_object_list, type)
        array = DataObjectArray.objects.create(is_array=True, type=type)
        for data_object in data_object_list:
            data_object.add_to_array(array)
        return array

    @classmethod
    def _validate_list(cls, data_object_list, type):
        for data_object in data_object_list:
            if not data_object.type == type:
                raise TypeMismatchError(
                    'Expected type "%s", but DataObject %s is type %s' \
                    % (type, data_object.id.hex, data_object.type))
            if data_object.is_array:
                raise NestedArraysError('Cannot nest DataObjectArrays')

    class Meta:
        abstract=True


class FileHash(BaseModel):

    value = models.CharField(max_length=255, null=True)
    function = models.CharField(max_length=255, null=True)
    file_data_object = models.ForeignKey(
        'FileDataObject', null=True, related_name='hashes')


class ArrayMembership(BaseModel):

    # ManyToMany relationship between arrays and their items
    array = models.ForeignKey('DataObject', related_name='array_members')
    item = models.ForeignKey('DataObject', related_name='in_arrays')
    order = models.IntegerField()

    class Meta:
        ordering = ['order',]


class FileLocation(BaseModel):

    datetime_created = models.DateTimeField(
        default=timezone.now, editable=False)
    file_url = models.CharField(max_length=1000)
    upload_status = models.CharField(
        max_length=255,
        default='incomplete',
        choices=(('incomplete', 'Incomplete'),
                 ('complete', 'Complete'),
                 ('failed', 'Failed')))

    @classmethod
    def create_location_for_import(cls, file_data_object):

        # Get path from root
        path = cls._get_path_for_import(file_data_object)

        # Add url prefix
        file_url = cls._add_url_prefix(path)

        location = cls(file_url=file_url,
                       upload_status='incomplete')
        location.save()

        # FileLocation shares any hashes attached to file
        for hash in file_data_object.hashes.all():
            FileLocationHash.objects.create(
                file_location=location,
                value = hash.value,
                function = hash.function
        )
        return location

    @classmethod
    def _get_file_root(cls):
        file_root = get_setting('FILE_ROOT')
        # Allow '~/path' home dir notation on local file server
        if get_setting('FILE_SERVER_TYPE') == 'LOCAL':
            file_root = os.path.expanduser(file_root)
        if not file_root.startswith('/'):
            raise RelativeFileRootError(
                'FILE_ROOT setting must be an absolute path. Found "%s" instead.' \
                % file_root)
        return file_root

    @classmethod
    def _get_path_for_import(cls, file_data_object):
        file_root = cls._get_file_root()
        if get_setting('KEEP_DUPLICATE_FILES') and get_setting('FORCE_RERUN'):
            # If both are True, we can organize the directory structure in
            # a human browsable way
            return os.path.join(
                file_root,
                cls._get_browsable_path(file_data_object),
                "%s-%s-%s" % (
                    timezone.now().strftime('%Y%m%d%H%M%S'),
                    file_data_object.id.hex,
                    file_data_object.filename
                )
            )
        elif get_setting('KEEP_DUPLICATE_FILES'):
            # Separate dirs for imported, results, logs.
            # Within each dir use a flat directory structure but give
            # files with identical content distinctive names
            return os.path.join(
                file_root,
                cls._get_path_by_source_type(file_data_object),
                '%s-%s-%s' % (
                    timezone.now().strftime('%Y%m%d%H%M%S'),
                    file_data_object.id.hex,
                    file_data_object.filename
                )
            )
        else:
            # Use a flat directory structure and use file names that
            # reflect content
            return os.path.join(
                file_root,
                '%s-%s' % (
                    file_data_object.get_hash().function,
                    file_data_object.get_hash().value
                )
            )

    @classmethod
    def _get_browsable_path(cls, file_data_object):
        """Create a path for a given file, in such a way
        that files end up being organized and browsable by run
        """
        if file_data_object.source_type == 'imported':
            return 'imported'
        
        if file_data_object.source_type == 'log':
            subdir = 'logs'
            task_run_attempt \
                = file_data_object.task_run_attempt_log_file.task_run_attempt
            
        elif file_data_object.source_type == 'result':
            subdir = 'work'
            task_run_attempt \
                = file_data_object.task_run_attempt_output.task_run_attempt
        else:
            raise InvalidSourceTypeError('Invalid source_type %s'
                            % file_data_object.source_type)

        task_run = task_run_attempt.task_run
        step_run = task_run.step_run

        path = os.path.join(
            "%s-%s" % (
                step_run.template.name,
                step_run.id.hex,
            ),
            "task-%s" % task_run.id.hex,
            "attempt-%s" % task_run_attempt.id.hex,
        )
        while step_run.parent is not None:
            step_run = step_run.parent
            path = os.path.join(
                "%s-%s" % (
                    step_run.template.name,
                    step_run.id.hex,
                ),
                path
            )
        return os.path.join('runs', path, subdir)

    @classmethod
    def _get_path_by_source_type(cls, file_data_object):
        source_type_to_path = {
            'imported': 'imported',
            'result': 'results',
            'log': 'logs'
        }
        return source_type_to_path[file_data_object.source_type]

    @classmethod
    def _add_url_prefix(cls, path):
        if not path.startswith('/'):
            raise RelativePathError(
                'Expected an absolute path but got path="%s"' % path)
        FILE_SERVER_TYPE = get_setting('FILE_SERVER_TYPE')
        if FILE_SERVER_TYPE == 'LOCAL':
            return 'file://' + path
        elif FILE_SERVER_TYPE == 'GOOGLE_CLOUD':
            return 'gs://' + get_setting('BUCKET_ID') + path
        else:
            raise InvalidFileServerTypeError(
                'Couldn\'t recognize value for setting FILE_SERVER_TYPE="%s"'\
                % FILE_SERVER_TYPE)


class FileLocationHash(BaseModel):

    # Same as FileHash, but associated with the FileLocation instead
    # of the FileDataObject

    value = models.CharField(max_length=255, null=True)
    function = models.CharField(max_length=255, null=True)
    file_location = models.ForeignKey(
        'FileLocation', null=True, related_name='hashes')
