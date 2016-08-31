from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import ProtectedError
from django.utils import timezone
import os
import uuid

from .base import BaseModel, BasePolymorphicModel
from analysis import get_setting


class DataObject(BasePolymorphicModel):
    """A reference to DataObjectContent. There can be many DataObjects
    referencing the same content. Keeping the DataObjects as separate
    entities makes it possible to keep provenance graphs separate even
    if they independently contain data with the same content.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    datetime_created = models.DateTimeField(default=timezone.now,
                                            editable=False)

    TYPE_CHOICES = (
        ('file', 'File'),
        ('boolean', 'Boolean'),
        ('string', 'String'),
        ('integer', 'Integer'),
        # ('float', 'Float'),
        # ('json', 'JSON'),
    )

    @property
    def type(self):
        return self.DATA_TYPE

    @classmethod
    def get_by_value(cls, value, type):
        # where value is a user input. In the case of Files,
        # this looks up an existing file. For other data types,
        # it creates a new object with the given value.
        return class_type_map[type].get_by_value(value)

    def get_display_value(self):
        # This is the value rendered in string representations of the object.
        # Same as substitution value for all data types except file.
        # Override in FileDataObject.
        return self.get_substitution_value()

    def get_substitution_value(self):
        # This is the value substituted into a command
        return self.get_content().get_substitution_value()


class DataObjectContent(BasePolymorphicModel):
    """A unit of data passed into or created by analysis steps.
    This may be a file or another supported type of data, or an 
    array of one of these. Multitable inheritance is needed since 
    a TaskDefinitionInput has a foreign key to DataObjectContent 
    of any type.
    """


class FileDataObject(DataObject):

    NAME_FIELD = 'file_content__filename'
    HASH_FIELD = 'file_content__unnamed_file_content__hash_value'
    DATA_TYPE = 'file'

    file_content = models.ForeignKey(
        'FileContent',
        related_name='file_data_object',
        on_delete=models.PROTECT,
        null=True)
    file_location = models.ForeignKey(
        'FileLocation',
        related_name='file_data_object',
        on_delete=models.PROTECT,
        null=True)
    source_type = models.CharField(
        max_length=255,
        default='imported',
        choices=(('imported', 'Imported'),
                 ('result', 'Result'),
                 ('log', 'Log'))
    )

    def get_content(self):
        return self.file_content

    @classmethod
    def get_by_value(cls, value):
        file_data_objects = cls.filter_by_name_or_id_or_hash(value)
        if not file_data_objects.count() == 1:
            raise Exception('Expected one file but found %s for value %s' % (len(file_data_objects), value))
        return file_data_objects.first()

    def get_display_value(self):
        # This is the used as a reference to the FileDataObject
        # in serialized data.
        if self.file_content is None:
            return ''
        return '%s@%s' % (self.file_content.filename, self.id.hex)

    @classmethod
    def query(cls, query_string):
        return cls.filter_by_name_or_id_or_hash(query_string)

    def is_ready(self):
        # Is upload complete?
        if self.file_location:
            return self.file_location.status == 'complete'
        else:
            return False

    def post_create(self):
        self.post_create_or_update()

    def post_update(self):
        self.post_create_or_update()

    def post_create_or_update(self):
        self.add_file_location()
        self.add_implicit_links()

    def add_implicit_links(self):
        # Link FileLocation and UnnamedFileContent.
        # This link can be inferred from the DataObject
        # and therefore does not need to be serializer,
        # but having the link simplifies lookup
        if self.file_location is None:
            return
        elif self.file_location.unnamed_file_content is None \
             and self.file_content is not None:
            # FileContent exists but link is missing. Create it.
            self.file_location.unnamed_file_content \
                = self.file_content.unnamed_file_content
            self.file_location.save()

    def add_file_location(self):
        # A FileLocation should be generated once file_content is set
        if self.file_content and not self.file_location:
            # If a file with identical content has already been uploaded,
            # re-use it if permitted by settings.
            if not get_setting('KEEP_DUPLICATE_FILES'):
                file_location = self.file_content.get_valid_location()
                if file_location is not None:
                    self.file_location = file_location
                    self.save()
                    return

            # No existing file to use. Create a new location for upload.
            self.file_location \
                = FileLocation.create_location_for_import(self)
            self.save()

    def delete(self):
        file_content = self.file_content
        file_location = self.file_location
        super(FileDataObject, self).delete()
        try:
            file_content.delete()
        except ProtectedError:
            # Content is referenced from another object.
            pass
        # Do not delete file_location until disk space can be freed.

    def get_provenance_data(self, files=None, tasks=None, edges=None):
        if files is None:
            files = set()
        if tasks is None:
            tasks = set()
        if edges is None:
            edges = set()

        files.add(self)
        try:
            task_run_attempt_output =  self.task_run_attempt_output
        except ObjectDoesNotExist:
            return files, tasks, edges

        task_run_attempt = task_run_attempt_output.task_run_attempt
        tasks.add(task_run_attempt)
        edges.add((task_run_attempt.id.hex, self.id.hex))
        task_run_attempt.get_provenance_data(files, tasks, edges)

        return files, tasks, edges

        """
        return {
            'files': [
                {'id': '1'},
                {'id': '2'},
                {'id': '3',
                 'task': 'a'},
                {'id': '4',
                 'task': 'b'},
                {'id': '5',
                 'task': 'c'}
            ],
            'tasks': [
                {'id': 'a',
                 'inputs': ['1']},
                    {'id': 'b',
                     'inputs': ['2']},
                    {'id': 'c',
                     'inputs': ['3', '4']}
            ]
        }
        """

class FileContent(DataObjectContent):
    """Represents a file, including its content (identified by a hash), its 
    file name, and user-defined metadata.
    """

    filename = models.CharField(max_length=255)
    unnamed_file_content = models.ForeignKey(
        'UnnamedFileContent',
        related_name='file_contents',
        on_delete=models.PROTECT)

    def get_substitution_value(self):
        return self.filename

    def get_valid_location(self):
        # This function will return a 'complete' location or return None.
        #
        # This function should only be called when KEEP_DUPLICATE_FILES is
        # false, in which case we expect just one location. However, if
        # multiple uploads are initialized at the same time from different
        # clients, it can result in multiple locations, any number of which
        # may be complete.
        # 
        # For that reason we return the first location with status 'complete'.
        #
        complete_locations = self.unnamed_file_content.file_locations.filter(
            status='complete')
        if complete_locations.count() == 0:
            return None
        else:
            return complete_locations.first()

    def delete(self):
        unnamed_file_content = self.unnamed_file_content
        super(FileContent, self).delete()
        try:
            unnamed_file_content.delete()
        except ProtectedError:
            # Content is referenced from another object.
            pass
        

class UnnamedFileContent(BaseModel):
    """Represents file content, identified by a hash. Ignores file name.
    """

    hash_value = models.CharField(max_length=255)
    hash_function = models.CharField(max_length=255)

    class Meta:
        unique_together= (('hash_value', 'hash_function'),)


class FileLocation(BaseModel):
    """Location of file content.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    datetime_created = models.DateTimeField(default=timezone.now,
                                            editable=False)
    
    url = models.CharField(max_length=1000)
    status = models.CharField(
        max_length=255,
        default='incomplete',
        choices=(('incomplete', 'Incomplete'),
                 ('complete', 'Complete'),
                 ('failed', 'Failed'))
    )
    
    # The relationship to unnamed_file_content is for internal use only,
    # not serialized or deserialized. This can be obtained through
    # file_location.file_data_object.file_content.unnamed_file_content
    # This is ManyToOne because while unnamed_file_content object is unique
    # for a given hash, there can be many copies of the same content saved
    # under different FileDataObjects and in different FileLocations.

    unnamed_file_content = models.ForeignKey(
        'UnnamedFileContent',
        null=True,
        related_name='file_locations',
        on_delete=models.PROTECT)

    @classmethod
    def create_location_for_import(cls, file_data_object):
        location = cls(
            url=cls._get_url(cls._get_path_for_import(file_data_object)),
        )
        location.save()
        return location

    @classmethod
    def _get_path_for_import(cls, file_data_object):
        if get_setting('KEEP_DUPLICATE_FILES') and get_setting('FORCE_RERUN'):
            # If both are True, we can organize the directory structure in
            # a human browsable way
            return os.path.join(
                '/',
                get_setting('FILE_ROOT'),
                cls._get_browsable_path(file_data_object),
                "%s-%s-%s" % (
                    timezone.now().strftime('%Y%m%d%H%M%S'),
                    file_data_object.id.hex,
                    file_data_object.file_content.filename
                )
            )
        elif get_setting('KEEP_DUPLICATE_FILES'):
            # Use a flat directory structure but give files with
            # identical content distinctive names
            return os.path.join(
                '/',
                get_setting('FILE_ROOT'),
                '%s-%s-%s' % (
                    timezone.now().strftime('%Y%m%d%H%M%S'),
                    file_data_object.id.hex,
                    file_data_object.file_content.filename
                )
            )
        else:
            # Use a flat directory structure and use file names that
            # reflect content
            return os.path.join(
                '/',
                get_setting('FILE_ROOT'),
                '%s-%s' % (
                    file_data_object.file_content.unnamed_file_content\
                    .hash_function,                    
                    file_data_object.file_content.unnamed_file_content\
                    .hash_value
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
            raise Exception('Unrecognized source_type %s'
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
    def _get_url(cls, path):
        FILE_SERVER_TYPE = get_setting('FILE_SERVER_TYPE')
        if FILE_SERVER_TYPE == 'LOCAL':
            return 'file://' + path
        elif FILE_SERVER_TYPE == 'GOOGLE_CLOUD':
            if get_setting('BUCKET_ID').strip() == '':
                raise Exception('Bucket ID is not set.')
            return 'gs://' + get_setting('BUCKET_ID') + path
        else:
            raise Exception(
                'Couldn\'t recognize value for setting FILE_SERVER_TYPE="%s"'\
                % FILE_SERVER_TYPE)


class FileImport(BaseModel):

    note = models.TextField(max_length=10000, null=True)
    source_url = models.TextField(max_length=1000)
    file_data_object = models.OneToOneField(
        'FileDataObject',
        related_name='file_import',
        on_delete=models.CASCADE)


class DatabaseDataObject(DataObject):

    def is_ready(self):
        # Always ready if it exists in the database
        return True

    class Meta:
        abstract = True


class StringDataObject(DatabaseDataObject):

    DATA_TYPE = 'string'

    string_content = models.OneToOneField(
        'StringContent',
        related_name='data_object',
        on_delete=models.PROTECT)
    
    def get_content(self):
        return self.string_content

    @classmethod
    def get_by_value(cls, value):
        content = StringContent(string_value=value)
        content.save()
        data_object = StringDataObject(string_content=content)
        data_object.save()
        return data_object
    
    def delete(self):
        content = self.string_content
        super(StringDataObject, self).delete()
        try:
            content.delete()
        except ProtectedError:
            # Content is referenced from another object.
            pass


class StringContent(DataObjectContent):

    string_value = models.TextField()

    def get_substitution_value(self):
        return self.string_value


class BooleanDataObject(DatabaseDataObject):

    DATA_TYPE = 'boolean'

    boolean_content = models.OneToOneField(
        'BooleanContent',
        related_name='data_object',
        on_delete=models.PROTECT)

    def get_content(self):
        return self.boolean_content

    @classmethod
    def get_by_value(cls, value):
        if value == 'true':
            bvalue = True
        elif value == 'false':
            bvalue = False
        else:
            raise Exception(
                'Could not parse boolean value "%s". Use "true" or "false".'\
                % value)

        content = BooleanContent(boolean_value=bvalue)
        content.save()
        data_object = BooleanDataObject(boolean_content=content)
        data_object.save()
        return data_object

    def delete(self):
        content = self.boolean_content
        super(BooleanDataObject, self).delete()
        try:
            content.delete()
        except ProtectedError:
            # Content is referenced from another object.
            pass


class BooleanContent(DataObjectContent):

    boolean_value = models.BooleanField()

    def get_substitution_value(self):
        return self.boolean_value


class IntegerDataObject(DatabaseDataObject):
    
    DATA_TYPE = 'integer'

    integer_content = models.OneToOneField(
        'IntegerContent',
        related_name='data_object',
        on_delete=models.PROTECT)
    
    def get_content(self):
        return self.integer_content

    @classmethod
    def get_by_value(cls, value):
        content = IntegerContent(integer_value=value)
        content.save()
        data_object = IntegerDataObject(integer_content=content)
        data_object.save()
        return data_object

    def delete(self):
        content = self.integer_content
        super(IntegerDataObject, self).delete()
        try:
            content.delete()
        except ProtectedError:
            # Content is referenced from another object.
            pass


class IntegerContent(DataObjectContent):

    integer_value = models.IntegerField()

    def get_substitution_value(self):
        return self.integer_value


class_type_map = {
    'file': FileDataObject,
    'boolean': BooleanDataObject,
    'string': StringDataObject,
    'integer': IntegerDataObject,
}
