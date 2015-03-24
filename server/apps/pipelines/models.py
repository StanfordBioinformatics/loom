from django.db import models

class Application(models.Model):
    comments = models.CharField(max_length=1000)
    name = models.CharField(max_length=40)
    docker_image = models.CharField(max_length=40)

class LocalFile(models.Model):
    comments = models.CharField(max_length=1000)
    name = models.CharField(max_length=40)
    path = models.CharField(max_length=1000)

class ExternalFileLocation(models.Model):
    comments = models.CharField(max_length=1000)
    path = models.CharField(max_length=1000)

class Import(models.Model):
    comments = models.CharField(max_length=1000)
    import_file = models.OneToOneField(LocalFile, related_name='import')
    source = models.OneToOneField(ExternalFileLocation)

class Export(models.Model):
    comments = models.CharField(max_length=1000)
    export_file = models.OneToOneField(LocalFile, related_name='export')
    destination = models.OneToOneField(ExternalFileLocation)

class SessionResources(models.Model):
    comments = models.CharField(max_length=1000)
    disk_space = models.CharField(max_length=40)
    memory = models.CharField(max_length=40)
    cores = models.PositiveIntegerField()

class TaskResources(models.Model):
    comments = models.CharField(max_length=1000)
    memory = models.CharField(max_length=40)
    cores = models.PositiveIntegerField()

class Step(models.Model):
    comments = models.CharField(max_length=1000)
    command = models.CharField(max_length=1024)
    application = models.ForeignKey(Application)
    input_files = models.ManyToManyField(LocalFile related_name = 'input_for_steps')
    output_files = models.ManyToOneField(LocalFile, related_name = 'output_from_step')
    resources = models.OneToOneField(TaskResources)

class Session(models.Model):
    comments = models.CharField(max_length=1000)
    imports = models.ManyToOneField(Import)
    exports = models.ManyToOneField(Export)
    steps = models.ManyToOneField(Step)
    session_resources = models.OneToOneField(SessionResources)

class Pipeline(models.Model):
    comments = models.CharField(max_length=1000)
    session = models.OneToOneField(Session)
