from datetime import datetime
from django.db import models
from immutable.models import ImmutableModel, MutableModel

# ----------
# FileRecipe and related classes.
# Excluding FileLocations, ResourceSets, or other classes that affect execution but will not change results.

class DataObject(ImmutableModel):
    """Base class to allow pointers to Files or FileRecipes. Not intended to be instantiated without a subclass."""

class File(DataObject):
    hash_value = models.CharField(max_length = 100)
    hash_function = models.CharField(max_length = 100)

class FileRecipe(DataObject):
    step = models.ForeignKey('Step')
    output_port = models.ForeignKey('OutputPort')

    def is_processed(self):
        return StepResult.objects.filter(step=self.step).filter(status="done").exists()

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
# Request and related classes

class Request(ImmutableModel):
    file_recipes = models.ManyToManyField('FileRecipe')
    resource_sets = models.ManyToManyField('ResourceSet')
    date = models.DateTimeField()
    requester = models.CharField(max_length = 100)

    @classmethod
    def create(cls, data_obj_or_json):
        data_obj = cls._any_to_obj(data_obj_or_json)
        if data_obj.get('date') is None:
            data_obj.update({'date': str(datetime.now())})
        return super(Request, cls).create(data_obj)

class ResourceSet(ImmutableModel):
    step = models.ForeignKey(Step)
    memory_bytes = models.BigIntegerField()
    cores = models.IntegerField()

# ----------
# FileLocation and subclasses

class FileLocation(MutableModel):
    """Base class to allow pointing to a URL, blob, file path, etc. Not intended to be instantiated without a subclass."""
    file = models.ForeignKey(File)

class AzureBlobLocation(FileLocation):
    storage_account = models.CharField(max_length = 100)
    container = models.CharField(max_length = 100)
    blob = models.CharField(max_length = 100)

class UrlLocation(FileLocation):
    url = models.CharField(max_length = 256)

class FilePathLocation(FileLocation):
    file_path = models.CharField(max_length = 256)

"""
# ----------
# Result and related classes

# TODO
class Result(ImmutableModel):
    run = models.ForeignKey(Run)
    step = models.ForeignKey(Step)
    input_file_recipes = models.ManyToManyField(FileRecipe)
    input_files = models.ManyToManyField(File, related_name='inputs')
    output_files = models.ManyToManyField(File, related_name='outputs')

# Run and related classes

# TODO
class Run(ImmutableModel):
    step = models.ForeignKey('Step')

# ----------
# FileImport and related classes

# TODO
class ImportRecipe(DataObject):
    source = models.ForeignKey(Location, related_name='source')
    destination = models.ForeignKey(Location, related_name='destination')
    
    def is_imported(self):
        return ImportResult.objects.filter(import_recipe=self).filter(status="done").exists()
    

class ImportRequest(ImmutableModel):
    import_recipe = models.ForeignKey(ImportRecipe)
    requester = models.CharField(max_length = 100)

class ImportResult(ImmutableModel):
    import_recipe = models.ForeignKey(ImportRecipe)
    file_imported = models.ForeignKey(File)
    status = models.CharField(max_length = 16)

class Import(ImmutableModel):
    import_recipe = models.ForeignKey(ImportRecipe)
    import_result = models.ForeignKey(ImportResult)

"""
