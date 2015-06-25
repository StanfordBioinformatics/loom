from datetime import datetime
from django.db import models
from immutable.models import ImmutableModel, MutableModel


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

class WorkInProgress(models.Model): 
    open_requests = models.ManyToManyField('Request')
    new_analyses = models.ManyToManyField('Analysis')
    new_steps = models.ManyToManyField('Step')

    @classmethod
    def get_wip(cls):
        objects = cls.objects.all()
        if len(objects) > 1:
            raise Exception('Error: More than 1 WorkInProgress objects exist. This should be a singleton.')
        elif len(objects) < 1:
            wip = WorkInProgress()
            wip.save()
            return wip
        else:
            return objects[0]

    @classmethod
    def add_open_request(cls, request):
        wip = cls.get_wip()
        wip.open_requests.add(request)
        for analysis in request.get_analyses():
            wip.add_new_analysis(analysis)

    @classmethod
    def add_new_analysis(cls, analysis):
        wip = cls.get_wip()
        wip.new_analyses.add(analysis)

# ---------------
# AnalysisRequest and related classes

class Request(MutableModel, NamedModel):
    _class_name = ('request', 'requests')
    analyses = models.ManyToManyField('Analysis')
    requester = models.CharField(max_length = 100)

    def get_analyses(self):
        return self.analyses.all()

class Analysis(MutableModel, NamedModel):
    _class_name = ('analysis', 'analyses')
    steps = models.ManyToManyField('Step')
    input_bindings = models.ManyToManyField('InputBinding')
    connectors = models.ManyToManyField('Connector')

    def get_ready_steps(self):
        pass

class Step(MutableModel, NamedModel):
    _class_name = ('step_template', 'step_templates')
    name = models.CharField(max_length = 256)
    input_ports = models.ManyToManyField('InputPort')
    output_ports = models.ManyToManyField('OutputPort')
    command = models.CharField(max_length = 256)
    environment = models.ForeignKey('Environment')

class Environment(MutableModel, NamedModel):
    _class_name = ('environment', 'environments')

class DockerImage(Environment, NamedModel):
    _class_name = ('docker_image', 'docker_images')
    docker_image = models.CharField(max_length = 100)

class OutputPort(MutableModel, NamedModel):
    _class_name = ('output_port', 'output_ports')

    # Relative path within the working directory where
    # a file will be found after a step executes
    name = models.CharField(max_length = 256)
    file_path = models.CharField(max_length = 256)

class InputPort(MutableModel, NamedModel):
    _class_name = ('input_port', 'input_ports')

    # Relative path within the working directory where
    # a file will be copied before a step is executed
    name = models.CharField(max_length = 256)
    file_path = models.CharField(max_length = 256)

class File(ImmutableModel, NamedModel):
    _class_name = ('file', 'files')

    hash_value = models.CharField(max_length = 100)
    hash_function = models.CharField(max_length = 100)

class InputBinding(MutableModel, NamedModel):
    _class_name = ('input_binding', 'input_bindings')

    file = models.ForeignKey('File')
    destination = models.ForeignKey('InputBindingDestination')

class Connector(MutableModel, NamedModel):
    source = models.ForeignKey('SourceStepAndPort')
    destination = models.ForeignKey('DestinationStepAndPort')

class PortPointer(MutableModel, NamedModel):
    step = models.CharField(max_length = 256)
    port = models.CharField(max_length = 256)

    class Meta:
        abstract = True

class InputBindingDestination(PortPointer):
    pass

class SourceStepAndPort(PortPointer):
    pass

class DestinationStepAndPort(PortPointer):
    pass


'''
# ----------
# FileRecipe and related classes.
# Excluding FileLocations, ResourceSets, or other classes that affect execution but will not change results.

class DataObject(ImmutableModel, NamedModel):
    _class_name = ('data_object', 'data_objects')

    """Base class to allow pointers to Files or FileRecipes. Not intended to be instantiated without a subclass."""

    # Warning -- When a field is defined on a base class, the null=False requirement may not be enforced.
    # To be safe, define the field on the child class.


class FileRecipe(DataObject, NamedModel):
    _class_name = ('file_recipe', 'file_recipes')

    analysis_definition = models.ForeignKey('AnalysisDefinition')
    output_port = models.ForeignKey('OutputPort')

    def is_processed(self):
        return StepRunRecord.objects.filter(step=self.step).filter(status="done").exists()

# ----------
# RequestRun and related classes

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
'''
