from datetime import datetime
from django.db import models
from immutable.models import ImmutableModel, MutableModel

# Abstract base classes
class DataObject(ImmutableModel):
    """Base class to allow pointers to Files, FileRecipes, or ImportRecipes. Not intended to be instantiated without a subclass."""

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

    def is_processed(self):
        return SessionResult.objects.filter(session_recipe=self.session_recipe).filter(status="done").exists()

class ImportRecipe(Ingredient):
    source = models.ForeignKey(Location, related_name='source')
    destination = models.ForeignKey(Location, related_name='destination')
    
    def is_imported(self):
        return ImportResult.objects.filter(import_recipe=self).filter(status="done").exists()
    
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
    status = models.CharField(max_length = 16)

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

class SessionRecipe(ImmutableModel):
    session_template = models.ForeignKey('SessionTemplate')
    input_bindings = models.ManyToManyField(InputBinding)
    
    def is_ready(self):
        """ Return True if all Ingredients pointed to by input Bindings satisfy one of the following conditions:
            - Ingredient is a File,
            - Ingredient is a FileRecipe AND FileRecipe.is_processed(),
            - Ingredient is an ImportRecipe AND ImportRecipe.is_imported()
        """
        for input_binding in self.input_bindings:
            ingredient = input_binding.ingredient
            try:
                file = ingredient.file
                continue
            except File.DoesNotExist:
                pass
            
            try:
                file_recipe = ingredient.filerecipe
                if file_recipe.is_processed():
                    continue
                else:
                    return False
            except FileRecipe.DoesNotExist:
                pass

            try:
                import_recipe = ingredient.importrecipe
                if import_recipe.is_imported():
                    continue
                else:
                    return False
            except ImportRecipe.DoesNotExist:
                pass
        
        return True
        
class SessionResult(ImmutableModel):
    session_run = models.ForeignKey(SessionRun)
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
