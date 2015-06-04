# Immutable Models

An Immutable Model holds content that never changes. The primary key for each object is based on a hash of its content. If the Immutable Model.create() method is called twice with the same content, only one instance will exist. 

Immutable Models can be serialized/deserialized as JSON, or translated to/from python structures (list/dict), without writing serializer code. ManyToMany relationships are represented as lists. ForeignKeys and OneToOne relationships are represented as dicts. Relationships must form a DAG, and relationships must be defined on the parent, not on the child.

Mutable Models implement the serialization/deserialization of ImmutableModels but do not use content-based primary keys. Duplicates may be created, each with its own primary key. Updates to mutable models are allowed.

When creating or updating a model, the order in JSON arrays and JSON objects (or in python lists and dicts) is ignored. The ManyToMany relationships created from lists will not have any particular order. For hashing a model, JSON arrays are sorted alphanumerically by the hash values of the members, and JSON objects are sorted by keys, so reordering contents of a JSON array or JSON object will produce a model with the same primary key.

Mutable Models may reference Immutable Models, but not the reverse. All references in an Immutable Model must be to an Immutable Model.

Inheritance is supported, either abstract or multitable. When creating a model from a JSON or python structure, if the model class is declared abstract, or if the JSON contains fields not found in the model, (Im)Mutable Models attempt to find a subclass that matches the fields.



## Model definitions
Model definitions use the standard django ORM, but models should inherit from immutable.models.ImmutableModel and MutableModel. No extra code is needed.

```
from immutable.models import ImmutableModel, MutableModel

class ImmutableChildExample(ImmutableModel):
    name = models.CharField(max_length=100)

class ImmutableParentExample(ImmutableModel):
    name = models.CharField(max_length=100)
    child = models.ForeignKey(ImmutableChildExample)
    children = models.ManyToManyField(ImmutableChildExample)

class MutableChildExample(MutableModel):
    name = models.CharField(max_length=100)

class MutableParentExample(MutableModel):
    name = models.CharField(max_length=100)
    child = models.ForeignKey(MutableChildExample)
    children = models.ManyToManyField(ImmutableChildExample)
```
## Example usage
Immutable Models can never change, so they have a restricted set of methods:
```
model.create(data_json)
model.to_json()
model.to_obj()
model.get_by_id(id)
```

If you call model.save(), an error will be raised. Models cannot be saved except through the create() method.

For Mutable Models edits can be made with the model.update() function.
```
model.update(data_json)
```
## Inheritance
Use multitable inheritance when you want a reference to one of several possible classes.
```
class Container(ImmutableModel):
    pass
    
class FilingCabinet(Container):
    folder_name = models.CharField(max_length = 20)
    
class Cabinet(Container):
    shelf_number = models.IntegerField()
    
class Stuff(MutableModel):
    description = models.CharField(max_length = 100)
    stored_in = models.ForeignKey(Container)
```
Provided that each of the child classes has a set of fields not contained in any of the siblings, you can define your JSON objects without specifying the class of the child.
```
>>> stuff_json = '{"description": "toothpick dispenser invoice", "stored_in": {"folder_name": "myStuff"}}'
>>> stuff = Stuff.create(stuff_json)
```
If you serialize this model, you can see that _id fields have been assigned.
```
>>> print stuff.to_json()

{"_id":1,"description":"toothpick dispenser invoice","stored_in":{"_id":"bd33a00064d8ec08ad23ee1041ffe46fb444eaa87744e18375f2714444032c92","folder_name":"myStuff"}}
``` 
Stuff references Container, and FilingCabinet is a subclass of Container. We can use downcast() to retrieve the FilingCabinet object via the relationship to Container..
```
>>> stuff = Stuff.get_by_id(1)
>>> print stuff.stored_in

Container object

>>> print stuff.stored_in.downcast()

FilingCabinet object

>>> print stuff.stored_in.downcast().folder_name

myStuff
``` 
