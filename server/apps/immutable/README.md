# Immutable models

Immutable Models hold content that never changes. The ID for each object is based on a hash of its content.

Immutable Models support relationships, even when objects are transferred between server instances. Since the primary key of an immutable model is the same if it is recreated in a new server, it will form relationships with the same objects as before, provided they have been created in the new environment.

Identical models originating from different sources will be treated as the same model. Only one instance exists, as long as the content is identical.

Immutable Models can be serialized as a JSON, with keys sorted and with no spacing between separators. (The primary key of the model is a hash of the JSON.)

Models can also be constructed from a JSON object.

Since Immutable Models can never change, they are very simple to work with. The only methods are:

```
model.create(data_json)
model.to_json()
model.to_obj()
```

If you call model.save(), an error will be raised. Models cannot be saved except through the create() method.

There is a corresponding class of Mutable Models that have the same JSON serialize/deserialize functionality, but which also allow models to be edited. Edits can be made through the django model inerface, or with the model.update() function.
```
model.update(data_json)
```

## Model definitions
Model definitions are very similar to standard django models. For example:

```
class SampleImmutableParent(ImmutableModel):
    name = models.CharField(max_length=100)
    validation_schema = {'type': 'object',
                         'properties': {
                             'name': {
                                 'type': 'string',
                             }
                         },
                         'additionalProperties': False
    }


class SampleImmutableChild(ImmutableModel):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(SampleImmutableParent, related_name='child')
    validation_schema = {'type': 'object',
                         'properties': {
                             'name': {
                                 'type': 'string',
                             },
                             'parent': {
                                 'type': 'object'
                             }
                         },
                         'additionalProperties': False
    }
```
