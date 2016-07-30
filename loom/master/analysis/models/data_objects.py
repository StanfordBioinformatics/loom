from django.db import models
from django.db.models import ProtectedError
from django.utils import timezone
import os
import uuid

from .base import BaseModel, BasePolymorphicModel
from analysis import get_setting
from analysis.signals import post_update, post_create


class DataObject(BasePolymorphicModel):
    """A reference to DataObjectContent. There can be many DataObjects
    referencing the same content. Keeping the DataObjects as separate
    entities makes it possible to keep provenance graphs separate even
    if they independently contain data with the same content.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    TYPE_CHOICES = (
        ('file', 'File'),
        ('boolean', 'Boolean'),
        ('string', 'String'),
        ('integer', 'Integer'),
        # ('float', 'Float'),
        # ('json', 'JSON'),
    )

    def get_type(self):
        return self.TYPE

    @classmethod
    def get_by_value(cls, value, type):
        return class_type_map[type].get_by_value(value)


class DataObjectContent(BasePolymorphicModel):
    """A unit of data passed into or created by analysis steps.
    This may be a file or another supported type of data, or an 
    array of one of these. Multitable inheritance is needed since 
    a TaskDefinitionInput has a foreign key to DataObjectContent 
    of any type.
    """


class FileDataObject(DataObject):

    NAME_FIELD = 'file_content__filename'
    TYPE = 'file'

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
    temp_file_location = models.ForeignKey(
        'FileLocation',
        related_name='file_data_object_as_temp',
        on_delete=models.PROTECT,
        null=True)

    def get_content(self):
        return self.file_content

    @classmethod
    def get_by_value(cls, value):
        file_data_objects = cls.get_by_name_and_full_id(value)
        assert len(file_data_objects) == 1
        return file_data_objects.first()

    def get_substitution_value(self):
        return self.file_content.get_substitution_value()

    def is_ready(self):
        if self.file_location:
            return self.file_location.status == 'complete'
        else:
            return False

    @classmethod
    def post_create_or_update(cls, sender, instance, **kwargs):
        cls.add_temp_file_location(sender, instance)
        cls.add_file_location(sender, instance)
        cls.add_implicit_links(sender, instance)

    @classmethod
    def add_implicit_links(cls, sender, instance):
        # Link FileLocation and UnnamedFileContent.
        # This link can be inferred from the DataObject
        # and therefore does not need to be serializer,
        # but having the link simplifies lookup
        if instance.file_location is None:
            return
        elif instance.file_location.unnamed_file_content is None \
             and instance.file_content is not None:
            # FileContent exists but link is missing. Create it.
            instance.file_location.unnamed_file_content \
                = instance.file_content.unnamed_file_content
            instance.file_location.save()

    @classmethod
    def add_temp_file_location(cls, sender, instance):
        # If there is no FileLocation, set a temporary one.
        # The client will need this to know upload destination, but we
        # can't create a permanent FileLocation until we know the file hash,
        # since it may be used in the name of the file location.
        if not instance.temp_file_location and not instance.file_location:
            instance.temp_file_location \
                = FileLocation.create_temp_file_location()
            instance.save()

    @classmethod
    def add_file_location(cls, sender, instance):
        # A FileLocation should be generated once file_content is set
        if instance.file_content and not instance.file_location:
            # If a file with identical content has already been uploaded,
            # re-use it if permitted by settings.
            if instance.file_content.has_location() \
               and not get_setting('KEEP_DUPLICATE_FILES'):
                instance.file_location \
                    = instance.file_content.get_location()
            else:
                instance.file_location \
                    = FileLocation.create_location_for_import(instance)

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


post_create.connect(FileDataObject.post_create_or_update, sender=FileDataObject)
post_update.connect(FileDataObject.post_create_or_update, sender=FileDataObject)


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

    def has_location(self):
        return self.unnamed_file_content.file_locations.count() > 0

    def get_location(self):
        location_count = self.unnamed_file_content.file_locations.count()
        assert location_count == 1, \
            "Expected 1 location but found %s for file %s" % \
            (location_count, self.filename)
        return self.unnamed_file_content.file_locations.first()

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
    url = models.CharField(max_length=1000)
    status = models.CharField(
        max_length=256,
        default='incomplete',
        choices=(('incomplete', 'Incomplete'),
                 ('complete', 'Complete'),
                 ('failed', 'Failed'))
    )            
    # The relationship to unnamed_file_content is for internal use only,
    # not serialized or deserialized. This can be obtained through
    # file_data_object.file_content.unnamed_file_content
    unnamed_file_content = models.ForeignKey(
        'UnnamedFileContent',
        null=True,
        related_name='file_locations',
        on_delete=models.SET_NULL)

    @classmethod
    def create_location_for_import(cls, file_data_object):
        location = cls(
            url=cls._get_url(cls._get_path_for_import(file_data_object)),
        )
        location.save()
        return location

    @classmethod
    def create_temp_file_location(cls):
        location = cls(url=cls._get_url(cls._get_temp_path_for_import()))
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
                    file_data_object.file_content.unnamed_file_content.hash_function,                    
                    file_data_object.file_content.unnamed_file_content.hash_value
                )
            )

    @classmethod
    def _get_browsable_path(cls, file_data_object):
        """Create a path for a given file, in such a way
        that files end up being organized and browsable by run
        """
        try:
            # Having a FileImport implies it is imported.
            file_data_object.file_import
            return 'imported'
        except FileImport.DoesNotExist:
            pass
        try:
            # Having a task_run_attempt_log_file implies it is a log
            task_run_attempt \
                = file_data_object.task_run_attempt_log_file.task_run_attempt
            subdir = 'logs'
        except AttributeError:
            try:
                # Having a task_run_attempt_output implies it is a result
                task_run_attempt \
                    = file_data_object.task_run_attempt_output.task_run_attempt
                subdir = 'work'
            except AttributeError:
                raise Exception(
                    "Could not classify FileDataObject %s as an import, "\
                    "log, or result" % file_data_object.id.hex)
            
        step_run = task_run_attempt.task_run.step_runs.first()
        assert task_run_attempt.task_run.step_runs.count() == 1
        path = os.path.join(
            "%s-%s" % (
                step_run.template.name,
                step_run.get_id(),
            ),
            "task-%s" % task_run_attempt.task_run.get_id(),
            "attempt-%s" % task_run_attempt.get_id(),
        )
        while step_run.parent_run is not None:
            step_run = step_run.parent_run
            path = os.path.join(
                "%s-%s" % (
                    step_run.template.name,
                    step_run.get_id(),
                ),
                path
            )
        return os.path.join('runs', path, subdir)

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
    type = models.CharField(
        max_length=256,
        default='import',
        choices=(('import', 'Import'),
                 ('result', 'Result'),
                 ('log', 'Log'))
    )


class DatabaseDataObject(DataObject):

    def is_ready(self):
        # Always ready if it exists in the database
        return True

    class Meta:
        abstract = True


class StringDataObject(DatabaseDataObject):

    TYPE = 'string'

    string_content = models.OneToOneField(
        'StringContent',
        related_name='data_object',
        on_delete=models.PROTECT)
    
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

    TYPE = 'boolean'

    boolean_content = models.OneToOneField(
        'BooleanContent',
        related_name='data_object',
        on_delete=models.PROTECT)

    def get_content(self):
        return self.boolean_content

    @classmethod
    def get_by_value(cls, value):
        if value == 'true':
            b = True
        elif value == 'false':
            b = False
        else:
            raise Exception(
                'Could not parse boolean value "%s". Use "true" or "false".'\
                % value)
        return cls.create(
            {
                'boolean_content': {
                    'boolean_value': b
                }
            }
        )

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
    
    TYPE = 'integer'

    integer_content = models.OneToOneField(
        'IntegerContent',
        related_name='data_object',
        on_delete=models.PROTECT)
    
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
