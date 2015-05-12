from django.db import models

# Ingredient and its subclasses
class Ingredient(models.Model):
    """Abstract base class to allow pointers to either Files or FileRecipes."""
    class Meta:
        abstract = True

class File(Ingredient):
    location = models.ForeignKey(Location)

class FileRecipe(Ingredient):
    from_run_recipe = models.ForeignKey(RunRecipe)
    from_port = models.ForeignKey(Port)

# Location and its subclasses
class Location(models.Model):
    """Abstract base class to allow pointing to a URL, blob, file path, etc."""
    class Meta:
        abstract = True

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
    port = models.ForeignKey(Port)

class Port(models.Model):
    from_session = models.ForeignKey(Session)

class Request(models.Model):
    file_recipes = models.ManyToManyField(FileRecipe)
    date = models.DateTimeField()
    requester = models.CharField(max_length = 100)

class Run(models.Model):
    run_recipe = models.ForeignKey(RunRecipe)
    run_result = models.ForeignKey(RunResult)

class RunRecipe(models.Model):
    sessions = models.ManyToManyField(Session)
    input_bindings = models.ManyToManyField(Binding)

class RunResult(models.Model):
    run_recipe = models.ForeignKey(RunResult)
    input_file_recipes = models.ManyToManyField(FileRecipe)
    input_files = models.ManyToManyField(File)
    output_files = models.ManyToManyField(File)

class Session(models.Model):
    steps = models.ManyToManyField(Step)
    
class Step(models.Model):
    docker_image = models.CharField(max_length = 100)
    command = models.CharField(max_length = 256)

