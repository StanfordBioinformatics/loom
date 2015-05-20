from django.db import models

# Abstract base classes
class Ingredient(models.Model):
    """Base class to allow pointers to Files, FileRecipes, or FileImports. Not intended to be instantiated without a subclass."""
    pass

class Location(models.Model):
    """Base class to allow pointing to a URL, blob, file path, etc. Not intended to be instantiated without a subclass."""
    pass

# Ingredient subclasses
class File(Ingredient):
    location = models.ForeignKey(Location)

class FileRecipe(Ingredient):
    from_run_recipe = models.ForeignKey('RunRecipe')
    from_port = models.ForeignKey('Port')

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
class Binding(models.Model):
    ingredient = models.ForeignKey(Ingredient)
    port = models.ForeignKey('Port')

class ImportRequest(models.Model):
    import_recipe = models.ForeignKey(ImportRecipe)

class ImportResult(models.Model):
    import_recipe = models.ForeignKey(ImportRecipe)
    file_imported = models.ForeignKey(File)

class Import(models.Model):
    import_recipe = models.ForeignKey(ImportRecipe)
    import_result = models.ForeignKey(ImportResult)

class Port(models.Model):
    from_session = models.ForeignKey('Session')

class Request(models.Model):
    file_recipes = models.ManyToManyField(FileRecipe)
    date = models.DateTimeField()
    requester = models.CharField(max_length = 100)

class Run(models.Model):
    run_recipe = models.ForeignKey('RunRecipe')
    run_result = models.ForeignKey('RunResult')

class RunRecipe(models.Model):
    sessions = models.ManyToManyField('Session')
    input_bindings = models.ManyToManyField(Binding)

class RunResult(models.Model):
    run_recipe = models.ForeignKey(RunRecipe)
    input_file_recipes = models.ManyToManyField(FileRecipe)
    input_files = models.ManyToManyField(File, related_name='inputs')
    output_files = models.ManyToManyField(File, related_name='outputs')

class Session(models.Model):
    steps = models.ManyToManyField('Step')
    
class Step(models.Model):
    docker_image = models.CharField(max_length = 100)
    command = models.CharField(max_length = 256)
