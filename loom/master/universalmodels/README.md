# Universal Models

Universal Models make it possible to serialize and deserialize database records with complex parent-child relationships, and to share data between databases while maintaining relations between objects.

## JSON serialization/deserialization
All models can be represented as a JSON for export/import without loss of information. In every relation, the parent is the model where the field is defined, and the child is the related model. When parents are serialized, they contain all of their children. When children are serialized, links to the parents are not included. In deserialization, a parent can create new children or link to existing models as children.

## Types of Universal Models
As described below, there are two kinds of Universal Models: InstanceModel and ImmutableModel.

### InstanceModel
Think of an InstanceModel as something that is unique because it was created at a particular point in time. Even if its content is the same as another object, the two are considered distinct. To ensure universal uniqueness, the primary key of an InstanceModel is a uuid.

An InstanceModel may be edited.

Consider the definition of two instance models below with a OneToOne relation.

```
class InstanceModelChild(InstanceModel):
    name = fields.CharField(max_length=100)

class InstanceModelParent(InstanceModel):
    name = fields.CharField(max_length=100)
    onetoonechild = fields.OneToOneField(
        InstanceModelChild,
        null=True,
        related_name = 'parent')
```

We can deserialize, serialize, and update the models as shown below:

```
>>> m = InstanceModelParent.create({"name": "The Parent", "onetoonechild": {"name": "The Only Child"}})
>>> m.to_json()
'{"_id":"4814a55a-6a8e-4db0-bb39-cb13b59422d8","datetime_created":"2016-01-27T02:47:14.642954+00:00","datetime_updated":"2016-01-27T02:47:14.650193+00:00","name":"The Parent","onetoonechild":{"_id":"c1e6216b-302a-4603-ac15-91f1f39e9794","datetime_created":"2016-01-27T02:47:14.644665+00:00","datetime_updated":"2016-01-27T02:47:14.644840+00:00","name":"The Only Child"}}'
>>> m.onetoonechild.update({"name": "Junior"})
<InstanceModelChild: InstanceModelChild object>
>>> m.to_json()
'{"_id":"c74a8e3e-079c-46a2-a1fd-b12371697e14","datetime_created":"2016-01-27T02:53:16.215665+00:00","datetime_updated":"2016-01-27T02:53:16.217730+00:00","name":"The Parent","onetoonechild":{"_id":"f35c6a5c-163e-498a-9d01-413f357835b0","datetime_created":"2016-01-27T02:53:16.216293+00:00","datetime_updated":"2016-01-27T02:53:26.177909+00:00","name":"Junior"}}'
```

### ImmutableModel
In contrast, immutable models are defined purely by the data they contain. If identical model data arises from two different sources, it is treated as a single model.

The primary key of an ImmutableModel is a hash of the model contents. If the same ImmutableModel exists in two different databases, even if it arose from two different sources, it will have the same primary key in both databases. If the contents of those databases are merged, that ImmutableModel will be represented as a single object, and it will become possible to look up related data that originated from either database.

Consider the ImmutableModel definitions below:

```
class ImmutableModelChild(ImmutableModel):
    name = fields.CharField(max_length=100)

class ImmutableModelParent(ImmutableModel):
    name = fields.CharField(max_length=100)
    manytoonechild = fields.ForeignKey(
        ImmutableModelChild,
        null=True,
        related_name = 'parents')
```

Let's create a parent and child, and note the primary key of the child.

```
>>> dad = ImmutableModelParent.create({"name": "Dad", "manytoonechild": {"name": "Daughter"}})
>>> dad.manytoonechild._id
'1573a84765092dca1a6ed14bb5c413932462919c1ae71b6268032a4bb1e6337e'
```

Now we define another parent and child, using exactly the same child definition:

```
>>> mom = ImmutableModelParent.create({"name": "Mom", "manytoonechild": {"name": "Daughter"}})
>>> mom.manytoonechild._id
'1573a84765092dca1a6ed14bb5c413932462919c1ae71b6268032a4bb1e6337e'
```

Although we didn't explicitly relate this to the first child definition, note that they have the same primary key. If you inspect the child object, it is clear that we have created a single child with two parents:

```
>>> daughter = mom.manytoonechild
>>> daughter.parents.count()
2
```

Immutable models cannot be edited. To change the contents, you will have to create a new model which will have a different primary key and will not preserve the relations to the original model.

### Relationship restrictions on Universal Models

Consider a parent-child relationship where the child is immutable. It is not possible to enforce a one-to-one relationship or a many-to-one relationship, because it is always possible for another model to be a parent of a child with identical content, in which case the child would have multiple parents. For ImmutableModel children, always use foreign key (i.e. many-to-one) or many-to-many relations.

An immutable model cannot contain (be a parent of) an InstanceModel, since instance models can be edited but immutable models cannot. However, an InstanceModel may contain (be parent of) an ImmutableModel.

# Inheritance

Multitable inheritance is supported, allowing a parent model to point to a base class, and thereby allowing different types of children to be linked to the same field on the parent. Abstract inheritance can also be used in model definitions, but the parent should point directly to one of the derived classes, never to the abstract base class.

## Abstract Inheritance

Use abstract inheritance when you want children to inherit properties or methods from a base class, but where all parent-child relationships will be defined with a specific derived class as the child.

Consider this example:

```
class AbstractBaseChild(ImmutableModel):
    name = fields.CharField(max_length=100)

    class Meta:
        abstract=True

class Son1(AbstractBaseChild):
    pass

class Son2(AbstractBaseChild):
    pass

class ParentOfAbstract(ImmutableModel):
    name = fields.CharField(max_length=100)
    son1 = fields.ForeignKey(Son1, related_name='parent')
```

In this case, no table is created for the abstract parent, and the foreign key is always for a Son1 model.

```
>>> parent = ParentOfAbstract.create({"name": "The Parent", "son1": {"name": "Jim"}})
>>> parent.son1
<Son1: Son1 object>
>>> parent.son1.to_json()
'{"_id":"fc146f9488b334f78b6479efe92895610e879e2826910d966ec0194fc128f8e6","name":"Jim"}'
```

## Multitable Inheritance

Use multitable inheritance when you want a model to reference to one of several possible model classes.

When deserializing a model, if the model is a base class, Universal Models will search for a derived class that matches the fields in the data. Types are not explicitly declared, and instead they are inferred from the data content. This behavior is the same on either immutable or instance models. The model schema must be designed to avoid ambiguous cases where it is not possible to determine which derived model to use based on the input data.

Consider these example model definitions with multitable inheritance. Note the "abstract=True" setting is missing from the base class. Also note that the parent can point to the base child class.

```
class MultiTableBaseChild(ImmutableModel):
    pass

class Daughter1(MultiTableBaseChild):
    daughter1_name = fields.CharField(max_length=100)

class Daughter2(MultiTableBaseChild):
    daughter2_name = fields.CharField(max_length=100)

class ParentOfMultiTable(ImmutableModel):
    name = fields.CharField(max_length=100)
    child = fields.ForeignKey(MultiTableBaseChild, related_name='parent')
```

We can create a parent and child in the same was as before.

```
parent = ParentOfMultiTable.create({"name": "The Parent", "child": {"daughter1_name": "Anita"}})
```

If you work with the model instance, you will see that the child has the derived Daughter1 class. Beware, though, if you reload the parent model then Django ORM will return the base class for the child field.

```
>>> parent.child
<Daughter1: Daughter1 object>
>>>reloaded_parent = ParentOfMultiTable.objects.get(_id=parent._id)
>>> reloaded_parent.child
<MultiTableBaseChild: MultiTableBaseChild object>
```

Universal Models include a "downcast" function that will return the model as the most derived class. Alternatively, use the 'get' function to get the child field, with the default option downcast=True.

```
>>> reloaded_parent.child.downcast()
<Daughter1: Daughter1 object>
>>> reloaded_parent.get('child')
<Daughter1: Daughter1 object>
```

## Universal Model methods

These methods are common to both instance models and immutable models:

```
MyModelClass.create(data_json_or_struct)
my_model.to_json()
my_model.to_struct()
my_model.get_by_id(id)
my_model.get(field_name)
model.get_field_as_struct(field_name)
lowest_derived_class_model = my_model.downcast()
MyModelClass.get_by_definition(data_json_or_struct)
```

The update method is unique to instance models:

```
my_model.update(data_json_or_struct)
```

The following methods are hooks that can be implemented by models that extend ImmutableModel or InstanceModel for custom validation:

```
def validate_model(self):
    '''Run custom model validation'''

def validate_create_input(cls, data_struct):
    '''Validate input data for a call to the "create" method'''
```

An InstanceModel can also be extended to validate input data for the "update" method:

```
def validate_patch_input(self, input):
    '''Validate input data for a call to the "update" method"'''
```
