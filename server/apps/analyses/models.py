from datetime import datetime
from django.db import models
from apps.immutable.models import ImmutableModel, MutableModel

# Abstract base classes
class Ingredient(ImmutableModel):
    """Base class to allow pointers to Files, FileRecipes, or ImportRecipes. Not intended to be instantiated without a subclass."""
    pass

class Location(ImmutableModel):
    """Base class to allow pointing to a URL, blob, file path, etc. Not intended to be instantiated without a subclass."""
    pass

class Hash(ImmutableModel):
    hash_value = models.CharField(max_length = 100)
    hash_function = models.CharField(max_length = 100)

# Ingredient subclasses
class File(Ingredient):
    location = models.ForeignKey(Location)
    hash = models.ForeignKey(Hash)

class FileRecipe(Ingredient):
    from_run_recipe = models.ForeignKey('SessionRecipe')
    from_port = models.ForeignKey('OutputPort')

class ImportRecipe(Ingredient):
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
    ingredient = models.ForeignKey(Ingredient)
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
    from_session = models.ForeignKey('Session')
    file_path = models.CharField(max_length = 256)

class InputPort(ImmutableModel):
    into_session = models.ForeignKey('Session')
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
    run_recipe = models.ForeignKey('SessionRecipe')
    run_result = models.ForeignKey('SessionResult')

class SessionRecipe(ImmutableModel):
    sessions = models.ManyToManyField('Session')
    input_bindings = models.ManyToManyField(InputBinding)

class SessionResult(ImmutableModel):
    run_recipe = models.ForeignKey(SessionRecipe)
    input_file_recipes = models.ManyToManyField(FileRecipe)
    input_files = models.ManyToManyField(File, related_name='inputs')
    output_files = models.ManyToManyField(File, related_name='outputs')

class Session(ImmutableModel):
    steps = models.ManyToManyField('Step')
    
class Step(ImmutableModel):
    docker_image = models.CharField(max_length = 100)
    command = models.CharField(max_length = 256)
