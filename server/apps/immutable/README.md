# Immutable models

Immutable Models hold content that never changes. The ID for each object is based on a hash of its content.

Immutable Models support relationships, even when objects are transferred between server instances. Since the primary key of an immutable model is the same if it is recreated in a new server, it will form relationships with the same objects as before, provided they have been created in the new environment. Supported relationship types are ForeignKey, OneToOne, and ManyToMany.

Identical models originating from different sources will be treated as the same model. Only one instance exists, as long as the content is identical.

Immutable Models support base classes, either as abstract base classes or using multitable models. When creating or updating a parent, the subclass of the child model is selected by matching fields from the JSON with fields on the model.

Immutable Models can be serialized/deserialized as a JSON. (The primary key of the model is a hash of the JSON, excluding the primary key _id field.)

Since Immutable Models can never change, they are very simple to work with. The only methods are:

```
model.create(data_json)
model.to_json()
model.to_obj()
model.get_by_id(id)
```

If you call model.save(), an error will be raised. Models cannot be saved except through the create() method.

There is a corresponding class of Mutable Models that have the same JSON serialize/deserialize functionality, but which also allow models to be edited. Edits can be made through the django model inerface, or with the model.update() function.
```
model.update(data_json)
```

## Model definitions
Model definitions are done as standard django models. For example:

```
class SampleImmutableParent(ImmutableModel):
    name = models.CharField(max_length=100)

class SampleImmutableChild(ImmutableModel):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(SampleImmutableParent, related_name='child')
```
