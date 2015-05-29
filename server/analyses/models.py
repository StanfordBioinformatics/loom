from datetime import datetime
from django.db import models
from immutable.models import ImmutableModel, MutableModel

# Abstract base classes
class DataObject(ImmutableModel):
    """Base class to allow pointers to Files, FileRecipes, or ImportRecipes. Not intended to be instantiated without a subclass."""
    pass

class Location(ImmutableModel):
    """Base class to allow pointing to a URL, blob, file path, etc. Not intended to be instantiated without a subclass."""
    file = models.ForeignKey('File')

# DataObject subclasses
class File(DataObject):
    hash_value = models.CharField(max_length = 100)
    hash_function = models.CharField(max_length = 100)

class FileRecipe(DataObject):
    session_recipe = models.ForeignKey('SessionRecipe')
    port = models.ForeignKey('OutputPort')

class ImportRecipe(DataObject):
    source = models.ForeignKey(Location, related_name='source')
    destination = models.ForeignKey(Location, related_name='destination')
    
# Location subclasses
class BlobLocation(Location):
    storage_account = models.CharField(max_length = 100)
    container = models.CharField(max_length = 100)
    blob = models.CharField(max_length = 100)

class UrlLocation(Location):
    url = models.CharField(max_length = 256)

class FilePathLocation(Location):
    file_path = models.CharField(max_length = 256)

# Other classes
class InputBinding(ImmutableModel):
    data_object = models.ForeignKey(DataObject)
    input_port = models.ForeignKey('InputPort')

class ImportRequest(ImmutableModel):
    import_recipe = models.ForeignKey(ImportRecipe)

class ImportResult(ImmutableModel):
    import_recipe = models.ForeignKey(ImportRecipe)
    file_imported = models.ForeignKey(File)

class Import(ImmutableModel):
    import_recipe = models.ForeignKey(ImportRecipe)
    import_result = models.ForeignKey(ImportResult)

class OutputPort(ImmutableModel):
    file_path = models.CharField(max_length = 256)

class InputPort(ImmutableModel):
    file_path = models.CharField(max_length = 256)

class Request(ImmutableModel):
    file_recipes = models.ManyToManyField(FileRecipe)
    date = models.DateTimeField()
    requester = models.CharField(max_length = 100)

    @classmethod
    def create(cls, data_obj_or_json):
        data_obj = cls._any_to_obj(data_obj_or_json)
        if data_obj.get('date') is None:
            data_obj.update({'date': str(datetime.now())})
        return super(Request, cls).create(data_obj)

class SessionRun(ImmutableModel):
    session_recipe = models.ForeignKey('SessionRecipe')
    session_result = models.ForeignKey('SessionResult')

class SessionRecipe(ImmutableModel):
    session_template = models.ForeignKey('SessionTemplate')
    input_bindings = models.ManyToManyField(InputBinding)

class SessionResult(ImmutableModel):
    session_recipe = models.ForeignKey(SessionRecipe)
    input_file_recipes = models.ManyToManyField(FileRecipe)
    input_files = models.ManyToManyField(File, related_name='inputs')
    output_files = models.ManyToManyField(File, related_name='outputs')

class SessionTemplate(ImmutableModel):
    models.ManyToMany()
    steps = models.ManyToManyField('Step')
    
class Step(ImmutableModel):
    docker_image = models.CharField(max_length = 100)
    command = models.CharField(max_length = 256)
