from datetime import datetime
from django.db import models
from immutable.models import ImmutableModel, MutableModel

# ----------
# FileRecipe and related classes.
# Excluding FileLocations, ResourceSets, or other classes that affect execution but will not change results.

class NamedModel(models.Model):
    _class_name = ('unnamed_model', 'unnamed_models') # To be overridden

    @classmethod
    def get_name(cls, plural=False):
        if plural:
            return cls._class_name[1]
        else:
            return cls._class_name[0]

    class Meta:
        abstract = True

class DataObject(ImmutableModel, NamedModel):
    _class_name = ('data_object', 'data_objects')

    """Base class to allow pointers to Files or FileRecipes. Not intended to be instantiated without a subclass."""

    # Warning -- When a field is defined on a base class, the null=False requirement may not be enforced.
    # To be safe, define the field on the child class.

class File(DataObject, NamedModel):
    _class_name = ('file', 'files')

    hash_value = models.CharField(max_length = 100)
    hash_function = models.CharField(max_length = 100)

class FileRecipe(DataObject, NamedModel):
    _class_name = ('file_recipe', 'file_recipes')

    analysis_definition = models.ForeignKey('AnalysisDefinition')
    output_port = models.ForeignKey('OutputPort')

    def is_processed(self):
        return StepRunRecord.objects.filter(step=self.step).filter(status="done").exists()

class InputBinding(ImmutableModel, NamedModel):
    _class_name = ('input_binding', 'input_bindings')

    data_object = models.ForeignKey(DataObject)
    input_port = models.ForeignKey('InputPort')

class OutputPort(ImmutableModel, NamedModel):
    _class_name = ('output_port', 'output_ports')

    # Relative path within the working directory where
    # a file will be found after a step executes
    file_path = models.CharField(max_length = 256)

class InputPort(ImmutableModel, NamedModel):
    _class_name = ('input_port', 'input_ports')

    # Relative path within the working directory where
    # a file will be copied before a step is executed
    file_path = models.CharField(max_length = 256)

class AnalysisDefinition(ImmutableModel, NamedModel):
    _class_name = ('analysis_definition', 'analysis_definitions')
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
        
class StepTemplate(ImmutableModel, NamedModel):
    _class_name = ('step_template', 'step_templates')
    input_ports = models.ManyToManyField('InputPort', related_name='step_templates')
    output_ports = models.ManyToManyField('OutputPort', related_name='step_templates')
    command = models.CharField(max_length = 256)
    environment = models.ForeignKey('Environment')

class Environment(ImmutableModel, NamedModel):
    _class_name = ('environment', 'environments')

class DockerImage(Environment, NamedModel):
    _class_name = ('docker_image', 'docker_images')
    docker_image = models.CharField(max_length = 100)

# ----------
# RequestRun and related classes

class RequestRun(MutableModel, NamedModel):
    _class_name = ('request_run', 'request_runs')
    analysis_definitions = models.ManyToManyField('AnalysisDefinition')
    analysis_runs = models.ManyToManyField('AnalysisRun')
    resource_set_requests = models.ManyToManyField('ResourceSetRequest')
    # TODO fix timestamps
#    date = models.DateTimeField()
    requester = models.CharField(max_length = 100)
    request_run_record = models.ForeignKey('RequestRunRecord', null=True)

    def is_ready_for_analysis_runs(self):
        # True if any analysis_definitions do not have completed analysis_runs
        for a in analysis_definitions:
            if not a.has_complete_analysis_run():
                return True
        return False
                
        

#    @classmethod
#    def create(cls, data_obj_or_json):
#        data_obj = cls._any_to_obj(data_obj_or_json)
#        if data_obj.get('date') is None:
#            data_obj.update({'date': str(datetime.now())})
#        return super(AnalysisRequest, cls).create(data_obj)

class RequestRunRecord(ImmutableModel, NamedModel):
    _class_name = ('request_run_record', 'request_run_records')
    analysis_run_records = models.ManyToManyField('AnalysisRunRecord')
    # TODO fix timestamps
#    date = models.DateTimeField()
    requester = models.CharField(max_length = 100)

class ResourceSetRequest(ImmutableModel, NamedModel):
    _class_name = ('resource_set_request', 'resource_set_requests')
    analysis_definition = models.ForeignKey(AnalysisDefinition)
    memory_bytes = models.BigIntegerField()
    cores = models.IntegerField()

# ----------
# StepDefinition and related classes

class StepDefinition(ImmutableModel, NamedModel):
    _class_name = ('step_definition', 'step_definitions')
    step_template = models.ForeignKey('StepTemplate')
    step_input_bindings = models.ManyToManyField('StepInputBinding')

class ResourceSet(ImmutableModel, NamedModel):
    _class_name = ('resource_set', 'resource_sets')
    step_definition = models.ForeignKey(StepDefinition)
    memory_bytes = models.BigIntegerField()
    cores = models.IntegerField()

class StepInputBinding(ImmutableModel, NamedModel):
    _class_name = ('step_input_binding', 'step_input_bindings')
    file = models.ForeignKey('File')
    input_port = models.ForeignKey('InputPort')
    
class StepResult(ImmutableModel, NamedModel):
    _class_name = ('step_result', 'step_results')
    step_definition = models.ForeignKey('StepDefinition')
    output_port = models.ForeignKey('OutputPort')
    file = models.ForeignKey('File')

# ----------
# FileLocation and subclasses

class FileLocation(MutableModel, NamedModel):
    _class_name = ('file_location', 'file_locations')
    """Base class to allow pointing to a URL, blob, file path, etc. Not intended to be instantiated without a subclass."""

class AzureBlobLocation(FileLocation, NamedModel):
    _class_name = ('azure_blob_location', 'azure_blob_locations')
    file = models.ForeignKey(File, null=True)
    storage_account = models.CharField(max_length = 100)
    container = models.CharField(max_length = 100)
    blob = models.CharField(max_length = 100)

class UrlLocation(FileLocation, NamedModel):
    _class_name = ('url_location', 'url_locations')
    file = models.ForeignKey(File, null=True)
    url = models.CharField(max_length = 256)

class FilePathLocation(FileLocation, NamedModel):
    _class_name = ('file_path_location', 'file_path_locations')
    file = models.ForeignKey(File, null=True)
    file_path = models.CharField(max_length = 256)

# ----------
# AnalysisRun and related classes

class StepRun(MutableModel, NamedModel):
    _class_name = ('step_run', 'step_runs')
    resource_set = models.ForeignKey('ResourceSet')
    step_definition = models.ForeignKey('StepDefinition')
    step_run_record = models.ForeignKey('StepRunRecord', null=True)
    step_results = models.ManyToManyField('StepResult')

class StepRunRecord(ImmutableModel, NamedModel):
    _class_name = ('step_run_record', 'step_run_records')
    resource_set = models.ForeignKey('ResourceSet')
    step_definition = models.ForeignKey('StepDefinition')
    step_results = models.ManyToManyField('StepResult')

class AnalysisRun(MutableModel, NamedModel):
    _class_name = ('analysis_run', 'analysis_runs')
    analysis_definition = models.ForeignKey('AnalysisDefinition')
    analysis_run_record = models.ForeignKey('AnalysisRunRecord', null=True)
    step_runs = models.ManyToManyField('StepRunRecord')

class AnalysisRunRecord(ImmutableModel, NamedModel):
    _class_name = ('analysis_run_record', 'analysis_run_records')
    step_run_records = models.ManyToManyField('StepRunRecord')
    analysis_definition = models.ForeignKey('AnalysisDefinition')
    
# ----------
# FileImport and related classes

class FileImportRequest(MutableModel, NamedModel):
    _class_name = ('file_import_request', 'file_import_requests')
    import_comments = models.CharField(max_length = 10000)
    file_location = models.ForeignKey('FileLocation')
    file_import_record = models.ForeignKey('FileImportRecord', null=True)
    requester = models.CharField(max_length = 100)
    
class FileImportRecord(ImmutableModel, NamedModel):
    _class_name = ('file_import_record', 'file_import_records')
    import_comments = models.CharField(max_length = 10000)
    file = models.ForeignKey('File')
    requester = models.CharField(max_length = 100)
