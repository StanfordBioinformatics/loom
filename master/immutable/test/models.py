from django.db import models
from immutable.models import ImmutableModel, MutableModel
from sortedm2m.fields import SortedManyToManyField

# Test models are defined here, not in the main app directory,
# to prevent creating the test models' database tables in a
# production database.

class BooleanModel(ImmutableModel):
    is_raining = models.BooleanField()

class SampleMutableChild(MutableModel):
    name = models.CharField(max_length=100)

class SampleMutableChild2(MutableModel):
    name = models.CharField(max_length=100)

class SampleMutableChild3(MutableModel):
    name = models.CharField(max_length=100)
    # This is illegal and will raise an error. Child cannot have foreign key to parent.
    parent = models.ForeignKey('SampleMutableParent', related_name='listofchildren_foreignkey', null=True)

class SampleMutableParent(MutableModel):
    FOREIGN_KEY_CHILDREN = ['listofchildren_foreignkey', 'singlechild']
    name = models.CharField(max_length=100)
    listofchildren = SortedManyToManyField(SampleMutableChild2)
    singlechild = models.ForeignKey(SampleMutableChild, null=True, related_name = 'parents')

class SampleMutableParentSorted(MutableModel):
    FOREIGN_KEY_CHILDREN = ['listofchildren_foreignkey', 'singlechild']
    name = models.CharField(max_length=100)
    listofchildren = SortedManyToManyField(SampleMutableChild2)
    singlechild = models.ForeignKey(SampleMutableChild, null=True, related_name = 'parents')

class SampleImmutableChild(ImmutableModel):
    name = models.CharField(max_length=100)

class SampleImmutableChild2(ImmutableModel):
    name = models.CharField(max_length=100)

class SampleImmutableParent(ImmutableModel):
    FOREIGN_KEY_CHILDREN = ['child']
    name = models.CharField(max_length=100)
    child = models.OneToOneField(SampleImmutableChild, related_name='parent', null=True)
    childlist = models.ManyToManyField(SampleImmutableChild2)

class SampleImmutableParentSorted(ImmutableModel):
    FOREIGN_KEY_CHILDREN = ['child']
    name = models.CharField(max_length=100)
    child = models.OneToOneField(SampleImmutableChild, related_name='parent', null=True)
    childlist = SortedManyToManyField(SampleImmutableChild2)

class SampleGrandparent(ImmutableModel):
    FOREIGN_KEY_CHILDREN = ['p1']
    p1 = models.OneToOneField('SampleImmutableParent', related_name='parent', null=True)

class BadMutableChild(MutableModel):
    name = models.CharField(max_length=100)

class BadImmutableParent(ImmutableModel):
    FOREIGN_KEY_CHILDREN = ['child']
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
    FOREIGN_KEY_CHILDREN = ['child']
    name = models.CharField(max_length=100)
    child = models.ForeignKey(AbstractBaseChild, related_name='parent')

class MultiTableBaseChild(ImmutableModel):
    pass

class Daughter1(MultiTableBaseChild):
    daughter1_name = models.CharField(max_length=100)

class Daughter2(MultiTableBaseChild):
    daughter2_name = models.CharField(max_length=100)

class ParentOfMultiTable(ImmutableModel):
    FOREIGN_KEY_CHILDREN = ['child']
    name = models.CharField(max_length=100)
    child = models.ForeignKey(MultiTableBaseChild, related_name='parent')
