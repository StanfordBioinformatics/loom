from datetime import datetime
from django.db import models
from immutable.models import ImmutableModel, MutableModel

# ----------
# FileRecipe and related classes.
# Excluding FileLocations, ResourceSets, or other classes that affect execution but will not change results.

class DataObject(ImmutableModel):
    """Base class to allow pointers to Files or FileRecipes. Not intended to be instantiated without a subclass."""

    # Warning -- When a field is defined on a base class, the null=False requirement may not be enforced.
    # To be safe, define the field on the child class.

class File(DataObject):
    hash_value = models.CharField(max_length = 100)
    hash_function = models.CharField(max_length = 100)

class FileRecipe(DataObject):
    step = models.ForeignKey('Step')
    output_port = models.ForeignKey('OutputPort')

    def is_processed(self):
        return StepRunRecord.objects.filter(step=self.step).filter(status="done").exists()

class InputBinding(ImmutableModel):
    data_object = models.ForeignKey(DataObject)
    input_port = models.ForeignKey('InputPort')

class OutputPort(ImmutableModel):
    # Relative path within the working directory where
    # a file will be found after a step executes
    file_path = models.CharField(max_length = 256)

class InputPort(ImmutableModel):
    # Relative path within the working directory where
    # a file will be copied before a step is executed
    file_path = models.CharField(max_length = 256)

class Step(ImmutableModel):
    step_template = models.ForeignKey('StepTemplate')
    input_bindings = models.ManyToManyField(InputBinding)
    
    def is_ready(self):
        """ Return True if all DataObjects pointed to by input Bindings satisfy one of the following conditions:
            - DataObject is a File,
            - DataObject is a FileRecipe AND FileRecipe.is_processed(),
            - DataObject is an ImportRecipe AND ImportRecipe.is_imported()
        """
        for input_binding in self.input_bindings:
            data_object = input_binding.data_object
            try:
                file = data_object.file
                continue
            except File.DoesNotExist:
                pass
            
            try:
                file_recipe = data_object.filerecipe
                if file_recipe.is_processed():
                    continue
                else:
                    return False
            except FileRecipe.DoesNotExist:
                pass

            try:
                import_recipe = data_object.importrecipe
                if import_recipe.is_imported():
                    continue
                else:
                    return False
            except ImportRecipe.DoesNotExist:
                pass
        
        return True
        
class StepTemplate(ImmutableModel):
    input_ports = models.ManyToManyField('InputPort', related_name='step_templates')
    output_ports = models.ManyToManyField('OutputPort', related_name='step_templates')
    command = models.CharField(max_length = 256)
    environment = models.ForeignKey('Environment')

class Environment(ImmutableModel):
    pass

class DockerImage(Environment):
    docker_image = models.CharField(max_length = 100)

# ----------
# AnalysisRequest and related classes

class AnalysisRequest(ImmutableModel):
    file_recipes = models.ManyToManyField('FileRecipe')
    resource_sets = models.ManyToManyField('ResourceSet')
    # TODO fix timestamps
#    date = models.DateTimeField()
    requester = models.CharField(max_length = 100)

#    @classmethod
#    def create(cls, data_obj_or_json):
#        data_obj = cls._any_to_obj(data_obj_or_json)
#        if data_obj.get('date') is None:
#            data_obj.update({'date': str(datetime.now())})
#        return super(AnalysisRequest, cls).create(data_obj)

class ResourceSet(ImmutableModel):
    step = models.ForeignKey(Step)
    memory_bytes = models.BigIntegerField()
    cores = models.IntegerField()

# ----------
# FileLocation and subclasses

class FileLocation(MutableModel):
    """Base class to allow pointing to a URL, blob, file path, etc. Not intended to be instantiated without a subclass."""

class AzureBlobLocation(FileLocation):
    file = models.ForeignKey(File)
    storage_account = models.CharField(max_length = 100)
    container = models.CharField(max_length = 100)
    blob = models.CharField(max_length = 100)

class UrlLocation(FileLocation):
    file = models.ForeignKey(File)
    url = models.CharField(max_length = 256)

class FilePathLocation(FileLocation):
    file = models.ForeignKey(File)
    file_path = models.CharField(max_length = 256)

# ----------
# AnalysisRun and related classes

class StepRun(MutableModel):
    step = models.ForeignKey('Step')
    step_run_record = models.ForeignKey('StepRunRecord', null=True)

class StepRunRecord(ImmutableModel):
    step = models.ForeignKey('Step')
    file = models.ForeignKey(File)

class AnalysisRun(MutableModel):
    analysis_request = models.ForeignKey('AnalysisRequest')
    analysis_run_record = models.ForeignKey('AnalysisRunRecord', null=True)

class AnalysisRunRecord(ImmutableModel):
    # TODO link AnalysisRunRecord.step_run_records[i].file to
    # the FileRecipes requested. Consider a case where
    # the same StepTemplate is used recursively so it
    # is not obvious which StepRunRecord belongs to the
    # top-level FileRecipe
    step_run_records = models.ManyToManyField('StepRunRecord')
    analysis_request = models.ForeignKey('AnalysisRequest')

# ----------
# FileImport and related classes

class FileImportRun(MutableModel):
    import_comments = models.CharField(max_length = 10000)
    destination = models.ForeignKey('FileLocation')
    file_import_record = models.ForeignKey('FileImportRecord', null=True)
    
class FileImportRecord(ImmutableModel):
    import_comments = models.CharField(max_length = 10000)
    file = models.ForeignKey('File')
