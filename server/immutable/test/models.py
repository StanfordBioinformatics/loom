from django.db import models
from immutable.models import ImmutableModel, MutableModel


# Test models are defined here, not in the main app directory,
# to prevent creating the test models' database tables in a
# production database.


class SampleMutableChild(MutableModel):
    name = models.CharField(max_length=100)

class SampleMutableChild2(MutableModel):
    name = models.CharField(max_length=100)

class SampleMutableChild3(MutableModel):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('SampleMutableParent', related_name='listofchildren_foreignkey')

class SampleMutableParent(MutableModel):
    name = models.CharField(max_length=100)
    listofchildren = models.ManyToManyField(SampleMutableChild2)
    singlechild = models.ForeignKey(SampleMutableChild, null=True)

class SampleImmutableChild(ImmutableModel):
    name = models.CharField(max_length=100)

class SampleImmutableParent(ImmutableModel):
    name = models.CharField(max_length=100)
    child = models.OneToOneField(SampleImmutableChild, related_name='parent')

class BadMutableChild(MutableModel):
    name = models.CharField(max_length=100)

class BadImmutableParent(ImmutableModel):
    name = models.CharField(max_length=100)
    child = models.OneToOneField(BadMutableChild, related_name='parent')

class AbstractBaseChild(ImmutableModel):
    class Meta:
        abstract=True

class Son1(AbstractBaseChild):
    son1_name = models.CharField(max_length=100)

class Son2(AbstractBaseChild):
    son2_name = models.CharField(max_length=100)

class ParentOfAbstract(ImmutableModel):
    name = models.CharField(max_length=100)
    child = models.ForeignKey(AbstractBaseChild, related_name='parent')

class MultiTableBaseChild(ImmutableModel):
    pass

class Daughter1(MultiTableBaseChild):
    daughter1_name = models.CharField(max_length=100)

class Daughter2(MultiTableBaseChild):
    daughter2_name = models.CharField(max_length=100)

class ParentOfMultiTable(ImmutableModel):
    name = models.CharField(max_length=100)
    child = models.ForeignKey(MultiTableBaseChild, related_name='parent')
