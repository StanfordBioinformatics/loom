from django.db import models
from universalmodels.models import ImmutableModel, InstanceModel
from universalmodels import fields

# Scratch

class ImmutableModelChild(ImmutableModel):
    name = fields.CharField(max_length=100)

class ImmutableModelParent(ImmutableModel):
    name = fields.CharField(max_length=100)
    manytoonechild = fields.ForeignKey(
        ImmutableModelChild,
        null=True,
        related_name = 'parents')


# Test models are defined here, not in the main app directory,
# to prevent creating the test models' database tables in a
# production database.

# Parent-child mutable models
    
class SampleInstanceModelChild(InstanceModel):
    name = fields.CharField(max_length=100)

class SampleInstanceModelChild2(InstanceModel):
    name = fields.CharField(max_length=100)

class SampleInstanceModelChild3(InstanceModel):
    name = fields.CharField(max_length=100)

class SampleInstanceModelChild4(InstanceModel):
    name = fields.CharField(max_length=100)

class SampleInstanceModelParent(InstanceModel):
    name = fields.CharField(max_length=100)
    onetoonechild = fields.OneToOneField(SampleInstanceModelChild, null=True, related_name = 'parent')
    onetomanychildren = fields.OneToManyField(SampleInstanceModelChild2, related_name='parent')
    manytomanychildren = fields.ManyToManyField(SampleInstanceModelChild3, related_name='parents')
    foreignkeychild = fields.ForeignKey(SampleInstanceModelChild4, null=True, related_name = 'parents')

# Parent-child immutable models
    
class SampleImmutableChild(ImmutableModel):
    name = fields.CharField(max_length=100)

class SampleImmutableChild2(ImmutableModel):
    name = fields.CharField(max_length=100)

class SampleImmutableChild3(ImmutableModel):
    name = fields.CharField(max_length=100)

class SampleImmutableChild4(ImmutableModel):
    name = fields.CharField(max_length=100)

class SampleImmutableParent(ImmutableModel):
    name = fields.CharField(max_length=100)
    manytomanychildren = fields.ManyToManyField(SampleImmutableChild3, related_name='parents')
    foreignkeychild = fields.ForeignKey(SampleImmutableChild4, null=True, related_name='parents')

class SampleImmutableParentInvalid(ImmutableModel):
    onetoonechild = fields.OneToOneField(SampleImmutableChild, null=True, related_name = 'parent')
    onetomanychildren = fields.OneToManyField(SampleImmutableChild2, related_name='parent')
    
# Abstract inheritance models
    
class AbstractBaseChild(ImmutableModel):
    name = fields.CharField(max_length=100)
    class Meta:
        abstract=True

class Son1(AbstractBaseChild):
    son1detail = fields.CharField(max_length=100)

class Son2(AbstractBaseChild):
    son2detail = fields.CharField(max_length=100)

class ParentOfAbstract(ImmutableModel):
    name = fields.CharField(max_length=100)
    son1 = fields.ForeignKey(Son1, related_name='parent')

# Multitable inheritance models
    
class MultiTableBaseChild(ImmutableModel):
    pass

class Daughter1(MultiTableBaseChild):
    daughter1_name = fields.CharField(max_length=100)

class Daughter2(MultiTableBaseChild):
    daughter2_name = fields.CharField(max_length=100)

class ParentOfMultiTable(ImmutableModel):
    name = fields.CharField(max_length=100)
    child = fields.ForeignKey(MultiTableBaseChild, related_name='parent')


# Supported non-relation fields

class NonRelationFieldsInstanceModel(InstanceModel):
    boolean_field = fields.BooleanField(null=True)
    json_field = fields.JSONField(null=True)
    char_field = fields.CharField(max_length=10)
    int_field = fields.IntegerField(null=True)
    
class BadImmutableParent(ImmutableModel):
    child = fields.ForeignKey(SampleInstanceModelChild, related_name='bad_parent')
