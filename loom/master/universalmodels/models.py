import datetime
import django
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db import transaction
from django.utils import timezone
import uuid

from .exceptions import *
from . import fields
from . import helpers


if not settings.USE_TZ == True:
    raise Error("Setting USE_TZ=True in the django settings module "\
                "is required, to support timezone-aware datetimes.")


class _BaseModel(models.Model):

    @classmethod
    def get_by_id(cls, _id):
        return cls.objects.get(_id=_id).downcast()

    @classmethod
    def get_by_definition(cls, data_struct_or_json):
        """Given a JSON or python structure as input,
        this method searches for that model in the database
        by id and, if found, returns the corresponding 
        ORM Model instance.
        """
        data_struct = cls._any_to_struct(data_struct_or_json)
        data_json = cls._any_to_json(data_struct_or_json)
        if data_struct.get('_id') is not None:
            model = cls.get_by_id(data_struct.get('_id'))
            from_db_struct = model.to_struct()
            from_db_json = cls._any_to_json(from_db_struct)
            if len(data_struct.keys()) > 1:
                # Unless only the ID field is given, all data must match
                if data_json != from_db_json:
                    raise Error('Found a model with matching id but contents do '\
                                'not match. Input model %s does not match model '\
                                'from database %s.' % (data_json, from_db_json))
            return model
        else:
            return None

    def get(self, field_name, downcast=True):
        """This convenience function looks up a child object
        by field and optionally downcasts it so that it will be 
        an instance of the lowest derived class.
        """
        model = self.downcast()
        field_value = getattr(model, field_name)
        if downcast:
            try:
                return field_value.downcast()
            except AttributeError:
                return field_value
        else:
            return field_value
        
    def to_json(self):
        """Render Model instance as JSON
        """
        struct = self.to_struct()
        return self._struct_to_json(struct)

    def to_struct(self):
        """Render Model instance as a python structure.
        This method is recursive. Any non-serializable values
        are converted to their serializable form.
        """

        struct = {}
        model = self.downcast()
        for field in model._get_nonparent_nonbase_fields():
            field_struct = model.get_field_as_struct(field)

            # Empty values are ignored when rendering a struct. This ensures the
            # intuitive behavior that a model created from
            # {'data1': 45, 'data2': None} is equivalent to a model created
            # from {'data1': 45}.
            #
            # (However, note that values of None and [] are significant when 
            # calling 'update'.)
            
            if field_struct in [None, [], '']:
                continue
            struct[field] = field_struct
        return struct

    def _get_nonparent_nonbase_fields(self):
        valid_fields = []
        for field in self._meta.get_fields():
            if self._is_field_a_parent(field.name):
                pass
            elif self._is_field_a_base_class(field.name):
                pass
            else:
                valid_fields.append(field.name)
        return valid_fields

    def _is_field_a_base_class(self, field):
        model = getattr(self, field)
        return isinstance(self, model.__class__)
    
    @classmethod
    def _struct_to_json(cls, data_struct):
        """Render python structure representation of a model
        as a JSON representation.
        """
        return helpers.struct_to_json(data_struct)

    @classmethod
    def _json_to_struct(cls, data_json):
        """Render JSON representation of a model
        as a python structure.
        """
        return helpers.json_to_struct(data_json)

    @classmethod
    def _any_to_json(cls, data):
        """Accept either a JSON or a python structure and
        return a JSON
        """
        if isinstance(data, basestring):
            # Input appears to be JSON. Round trip to validate.
            data_struct = cls._json_to_struct(data)
            return cls._struct_to_json(data_struct)
        else:
            # Assume input is a python structure. Convert to JSON.
            return cls._struct_to_json(data)

    @classmethod
    def _any_to_struct(cls, data):
        """Accept either a JSON or a python structure and
        return a python structure
        """
        if isinstance(data, basestring):
            # Input appears to be JSON. Convert to python structure.
            return cls._json_to_struct(data)
        else:
            # Input appears to be a python stucture.
            # Round trip to validate.
            data_json = cls._struct_to_json(data)
            return cls._json_to_struct(data_json)

    def _create_or_update_fields(self, data_struct):
        """Given the dict 'data_struct' as input, write its data to
        the fields of the current ORM model (self)
        """
        self._verify_dict(data_struct)
        self.unsaved_x_to_many_related_objects = {}
        for (key, value) in data_struct.iteritems():
            self._create_or_update_field(key, value)
        self._set_datetime_updated()
        models.Model.save(self)
        self._save_x_to_many_related_objects()

    def _save_x_to_many_related_objects(self):
        """Cannot create one-to-many or many-to-many relations until
        both models are saved, but saving the model before defining
        other fields can raise errors if those fields are required
        (i.e. null=False).
        
        Now that all other fields are added and the model is saved,
        we add x-to-many relations.
        """
        while self.unsaved_x_to_many_related_objects:
            (key, children) = self.unsaved_x_to_many_related_objects.\
                              popitem()
            field = getattr(self, key)
            field.clear()
            for child in children:
                field.add(child)

    def _set_datetime_updated(self):
        # Override if needed in child
        pass

    def _create_or_update_field(self, key, value):
        """Assign the data in 'value' to the field named 'key'
        """

        # If child definition includes data for a parent object, raise
        # an error.
        self._verify_field_is_not_a_parent(key)
        self._verify_relation_is_legal(key)
        
        if self._is_x_to_many_field(key):
            self._create_or_update_x_to_many_field(key, value)
        elif self._is_x_to_one_field(key):
            self._create_or_update_x_to_one_field(key, value)
        elif self._is_supported_nonrelation_field(key):
            self._create_or_update_nonrelation_field(key, value)
        else:
            field = self._meta.get_field(key)
            raise UnsupportedFieldTypeError(
                "Unsupported field type %s on field %s of model %s"
                % (field.__class__.__name__, key, self))
        
    def _is_x_to_many_field(self, key):
        field = self._meta.get_field(key)
        return isinstance(field, fields.OneToManyField) or \
            isinstance(field, fields.ManyToManyField)

    def _is_x_to_one_field(self, key):
        field = self._meta.get_field(key)
        return isinstance(field, fields.OneToOneField) or \
            isinstance(field, fields.ForeignKey)

    def _is_one_to_x_field(self, key):
        field = self._meta.get_field(key)
        return isinstance(field, fields.OneToManyField) or \
            isinstance(field, fields.OneToOneField)

    def _is_json_field(self, key):
        field = self._meta.get_field(key)
        return isinstance(field, fields.JSONField)

    def _is_supported_nonrelation_field(self, key):
        SUPPORTED_NONRELATION_FIELD_CLASSES = [
            fields.BooleanField,
            fields.CharField,
            fields.DateTimeField,
            fields.IntegerField,
            fields.JSONField,
            fields.TextField,
            fields.UUIDField
        ]
        field_class = self._meta.get_field(key).__class__
        return field_class in SUPPORTED_NONRELATION_FIELD_CLASSES

    def _create_or_update_x_to_many_field(self, key, valuelist):
        # Cannot create x-to-many relation until model is
        # saved, so we keep a list to save later.
        unsaved_for_this_key = self.unsaved_x_to_many_related_objects.\
                               setdefault(key, [])
        if valuelist is None:
            # This will remove all objects from this relation
            return
        self._verify_list_input(self, valuelist)
        for valuedict in valuelist:
            child = self._create_or_update_child(key, valuedict)
            unsaved_for_this_key.append(child)

    def _create_or_update_x_to_one_field(self, key, valuedict):
        if valuedict is None:
            setattr(self, key, None)
            return
        else:
            child = self._create_or_update_child(key, valuedict)
            setattr(self, key, child)

    @classmethod
    def _verify_x_to_one_child_is_legal(cls, parent_class):
        """Override for verification in subclasses
        """
        pass
            
    def _create_or_update_nonrelation_field(self, key, value):
        """Handle all supported nonrelation field types. This includes JSONField
        """
        self._verify_nonrelation_input(key, value)
        try:
            setattr(self, key, value)
        except:
            raise InvalidInputError(
                'Unable to set field %s to value %s on model %s'
                % (key, value, self))

    def _verify_field_is_not_a_parent(self, key):
        if self._is_field_a_parent(key):
            raise ParentNestedInChildError(
                "Setting field %s on class %s is not permitted because the "\
                "field is a parent." % (key, self.__class__.__name__))

    def _verify_relation_is_legal(self, key):
        if self._is_one_to_x_field(key):
            self._meta.get_field(key).related_model.\
                _verify_x_to_one_child_is_legal(self.__class__)
        
    def _verify_list_input(self, key, value):
        if not isinstance(value, list):
            raise InvalidInputTypeError(
                "Invalid input %s for field %s on model class %s. "\
                "List is required." % (value, key, self.__class__.__name__))

    def _verify_dict_input(self, key, value):
        if not isinstance(value, dict):
            raise InvalidInputTypeError(
                "Invalid input %s for field %s on model class %s. "\
                "Dict is required." % (value, key, self.__class__.__name__))

    def _verify_nonrelation_input(self, key, value):
        if self._is_json_field(key):
            pass
        elif isinstance(value, list) or isinstance(value, dict):
            raise InvalidInputTypeError(
                "Invalid input %s for field %s on model class %s."
                % (value, key, self.__class__.__name__))

    def _verify_dict(self, value):
        if not isinstance(value, dict):
            raise InvalidInputTypeError(
                'Expected input of type dict, but got %s' % value
            )

    def _create_or_update_child(self, key, value):
        """As part of updating the current model, create or
        update its children. This is related via an x-to-many
        or one-to-one relationship.
        """
        self._verify_dict_input(key, value)
        Model = self._get_model_for_field_name(key, value)
        if value.get('_id') is None:
            # No ID found, this is a new model. Create it from scratch.
            child = Model.create(value)
        else:
            child = Model.objects.get(_id=value.get('_id'))
            if isinstance(child, InstanceModel):
                # ID matches existing InstanceModel. Update it with new data.
                child.update(value)
                # Warning - this may overwrite the child model even when
                # calling "create" if the ID matches an existing model
            elif isinstance(child, ImmutableModel):
                # ID matches existing ImmutableModel. ImmutableModels can't
                # change, so no work to do here. But we want to raise an error
                # if it seems the user is trying to change the model.
                #
                
                # TODO: Allow a model with '_id' and no other fields
                
                if value.get('_id') != \
                   ImmutableModel._calculate_unique_id(value):
                    raise AttemptedToUpdateImmutableError(
                        "Attempted to update an immutable object. "\
                        "Original: '%s'. Update: '%s'"
                        % (child.to_struct(), value))
            else:
                raise Error(
                    "All model classes must extend ImmutableModel or "\
                    "InstanceModel. Neither class found for %s." % child)
        return child

    def _get_model_for_field_name(self, key, child_value):
        """Select the child model self.{key}
        """
        field = self._meta.get_field(key)
        Model = field.related.model
        if Model._is_abstract(child_value):
            # If child model is abstract or is missing fields contained in the
            # input, look for a subclass of the child that matches child_value
            child_fields = child_value.keys()
            Model = Model._select_best_subclass_model_by_fields(child_fields)
        self._check_child_compatibility(Model)
        return Model

    def _check_child_compatibility(self, Child):
        """Error if Child is not compatible with parent model (self)
        This is overridden in ImmutableModel
        """
        pass
    
    @classmethod
    def _is_abstract(cls, data_struct):
        """Detect if the class has subclass, either through abstract 
        inheritance or multitable inheritance.

        _do_all_fields_match will be true for multitable base classes if 
        all fields in data_struct are also defined in the base class.

        This method fails to identify a subclass as abstract if 1) it uses 
        multitable inheritance but the child adds no new fields, or 2) if the 
        input data uses only fields that exist in the parent and none that are 
        unique to the child. Those cases are unsupported.
        """
        return cls._meta.abstract or not cls._do_all_fields_match(data_struct)

    @classmethod
    def _select_best_subclass_model_by_fields(AbstractModel, fields):
        """Find a model that extends AbstractModel and matches the
        fields found in the data object.
        If more than one match are found, rase an exception.
        This works for either an abstract base class or a 
        multitable base class.
        """
        subclass_models = []
        for Model in django.apps.apps.get_models():
            if issubclass(Model, AbstractModel):
                subclass_models.append(Model)
        matching_models = []
        for Model in subclass_models:
            if Model._do_all_fields_match(fields):
                matching_models.append(Model)
        if len(matching_models) == 0:
            raise CouldNotFindSubclassError(
                "Failed to find a subclass of model %s that matches "\
                "these fields: %s" % (AbstractModel.__name__, fields))
        elif len(matching_models) > 1:
            raise CouldNotFindUniqueSubclassError(
                "Failed to find a unique subclass of model %s that "\
                "matches these fields: %s. Multiple models matched: %s"
                % (AbstractModel.__name__, fields.keys(), matching_models))
        else:
            # Successfully found one match
            return matching_models[0]
                
    @classmethod
    def _do_all_fields_match(cls, fields):
        """Returns true if all candidate fields are found on this model
        """
        return set(fields).issubset(set(cls._meta.get_all_field_names()))
        
    def downcast(self):
        """ Return the most derived class of this model with the same ID as 
        self. If no derived instances exist, return self.
        """
        derived_models = []
        for field in self._get_derived_class_field_names():
            try:
                model = getattr(self, field.name)
                if model._id == self._id:
                    derived_models.append(model)
            except ObjectDoesNotExist:
                # The base class model doesn't have a corresponding derived
                # class instance in this field.
                # Keep looking elsewhere.
                pass
        if len(derived_models) == 0:
            # There are no instances of this model in derived classes. It is
            # already downcast as far as possible.
            # Break out of recursive downcast.
            return self
        elif len(derived_models) > 1:
            raise Error("%s subclasses instances exist for abstract model "\
                        "%s. There should only be one."
                        % (len(submodels), self))
        else:
            # Proceed recursively until no more downcasting is possible.
            return derived_models[0].downcast()

    def _get_derived_class_field_names(self):
        """This function returns the name of any fields that represent
        derived model classes.

        If you define a BaseModel and extend it with 
        DerivedModel(BaseModel) using multitable inheritance 
        (i.e. _meta.abstract=False), one of the fields on a base BaseModel 
        instance is derivedmodel, and its value is the DerivedModel class. This 
        function returns fieldnames like the derivedmodel field in this example.

        This does not apply to abstract inheritance, since you cannot 
        instantiate an instance of the abstract base class.
        """

        derived_model_fields = []
        for field in self._meta.get_fields():
            if isinstance(field, models.fields.related.OneToOneRel) and \
                    issubclass(field.related_model, self.__class__):
                derived_model_fields.append(field)
        return derived_model_fields

    def get_field_as_struct(self, field):
        """Returns only the data stored under field as a python structure.
        This is used recursively with to_struct to render a full model and its
        children.
        """
        if self._is_x_to_many_field(field):
            return self._get_x_to_many_field_as_struct(field)
        elif self._is_x_to_one_field(field):
            return self._get_x_to_one_field_as_struct(field)
        elif self._is_supported_nonrelation_field(field):
            return self._get_supported_nonrelation_field_as_struct(field)
        else:
            raise UnsupportedFieldTypeError(
                'Unsupported field type %s' % field.__class__)
                
    def _is_field_a_parent(self, field_name):
        if not self._meta.get_field(field_name).is_relation:
            # This is a simple property, not a relationship field
            return False
        # Relationship fields are defined on the parent, so auto_created==True
        # indicates that the field points to a child, and self is the parent.
        return self._meta.get_field(field_name).auto_created

    def _get_x_to_many_field_as_struct(self, field):
        """Return the contents of models related by a one-to-many or 
        many-to-many field.
        """
        related_model_list = getattr(self, field)
        related_model_struct = []
        for model in related_model_list.iterator():
            related_model_struct.append(model.to_struct())
        return related_model_struct


    def _get_x_to_one_field_as_struct(self, field):
        """Returns the contents of model related by a one-to-one field
        """
        related_model = getattr(self, field)
        if related_model == None:
            return None
        else:
            return related_model.downcast().to_struct()

    def _get_supported_nonrelation_field_as_struct(self, field):
        return helpers.NonserializableTypeConverter.convert(
            getattr(self, field))
        
    def validate_model(self):
        """This can be overridden in the model definitions to include a
        validation routine for that specific model.
        """
        pass

    class Meta:
        abstract = True

class InstanceModel(_BaseModel):

    """Instance models use a UUID as their primary key, making their _id 
    value globally unique. They can be updated after creation, in contrast 
    to ImmutableModels where the primary key is a hash of the contents.
    """
    _id = models.UUIDField(primary_key=True, default=lambda: uuid.uuid4().hex,
                           editable=False)
    datetime_created = fields.DateTimeField(default=timezone.now)
    datetime_updated = fields.DateTimeField(default=timezone.now)

    @classmethod
    def create(cls, data_struct_or_json):
        """Use a JSON or python structure to create a model and save 
        it to the database"""
        data_struct = cls._any_to_struct(data_struct_or_json)
        cls.validate_create_input(data_struct)
        # If inheritance is used, create the model instance using the
        # most derived class that matches the fields in the input.
        Model = cls._select_best_subclass_model_by_fields(data_struct)
        # Use a transaction for creation of the model and any children
        with transaction.atomic():
            o = Model()
            o._create_or_update_fields(data_struct)
            o.validate_model()
        return o

    def update(self, update_json):
        """Use a JSON or python structure to update an existing model and
        save it to the database.
        """
        update_struct = self._any_to_struct(update_json)
        self._verify_update_id_matches_model(update_struct.get('_id'))
        # Start with existing model as a dict and update any fields that
        # are contained in update_json
        self.validate_patch_input(update_struct)
        model_struct = self.to_struct()
        model_struct.update(update_struct)
        # Use a transaction for update of the model and any children
        with transaction.atomic():
            self._create_or_update_fields(model_struct)
            self.validate_model()
        return self

    @classmethod
    def validate_create_input(cls, data_struct):
        """This can be overridden in the model definitions to include a
        validation routine for that specific model.
        """
        pass

    def validate_patch_input(self, data_struct):
        """This can be overridden in the model definitions to include a
        validation routine for that specific model.
        """
        pass

    def _set_datetime_updated(self):
        self.datetime_updated = timezone.now()
        
    def _verify_update_id_matches_model(self, _id):
        if _id is None:
            return
        if uuid.UUID(str(_id)) != uuid.UUID(str(self._id)):
            raise UpdateIdMismatchError(
                'Update does not match model. The update JSON gave an _id '\
                'of "%s", but this model has _id "%s."' % (_id, self._id))

    class Meta:
        abstract = True

class ImmutableModel(_BaseModel):

    _id = models.CharField(primary_key=True, max_length=255)

    @classmethod
    def create(cls, data_struct_or_json):
        """Use a JSON or python structure to create a model and save 
        it to the database"""
        data_struct = cls._any_to_struct(data_struct_or_json)
        cls.validate_create_input(data_struct)
        _id = cls._verify_input_id_matches_hash(data_struct)
        data_struct.update({'_id': _id})
        # If inheritance is used, create the model instance using the
        # most derived class that matches the fields in the input.
        Model = cls._select_best_subclass_model_by_fields(data_struct)
        # Use a transaction for creation of the model and any children
        with transaction.atomic():
            o = Model()
            o._create_or_update_fields(data_struct)
            o.validate_model()
        return o
            
    @classmethod
    def validate_create_input(cls, data_struct):
        """This can be overridden in the model definitions to include a
        validation routine for that specific model.
        """
        pass

    @classmethod
    def _verify_input_id_matches_hash(cls, data_struct):
        id_from_input = data_struct.get('_id')
        _id = cls._calculate_unique_id(data_struct)
        if id_from_input is not None:
            if id_from_input != _id:
                raise UniqueIdMismatchError(
                    "The input _id %s is out of sync with the hash of "\
                    "contents %s on model %s"
                    %(id_from_input, data_struct, cls.__name__))
        return _id

    @classmethod
    def _verify_x_to_one_child_is_legal(cls, parent_class):
        raise IllegalRelationError(
            'Many-to-one and one-to-one relationships cannot have immutable '\
            'children. Immutable models can always have multiple parents. '\
            'Check the relationship of %s to %s.'
            % (parent_class.__name__, cls.__name__))
        
    def save(self):
        raise NoSaveAllowedError(
            "Immutable models cannot be saved after creation.")

    @classmethod
    def get_by_definition(cls, data_struct_or_json):
        id = cls._calculate_unique_id(data_struct_or_json)
        return cls.get_by_id(id)

    @classmethod
    def _calculate_unique_id(cls, data_struct_or_json):
        data_struct = cls._any_to_struct(data_struct_or_json)
        return helpers.IdCalculator(data_struct=data_struct, id_key='_id').get_id()

    def _check_child_compatibility(self, Child):
        """Verify that all children are also Immutable. Since Immutable 
        models are a hash of their contents, none of their contents, 
        including the contents of their children, can change.
        """
        if not issubclass(Child, ImmutableModel):
            raise InstanceModelChildError(
                "An ImmutableModel can only contain references to " \
                "ImmutableModels. A %s cannot contain a %s."
                % (type(self), Child))

    def _check_foreign_key_compatibility(self, Child):
        """Since immutable models are a hash of their content, the same model 
        can arise twice from different sources and be the same object in the 
        database. For that reason, there are no one-to-many or many-to-one 
        models, only many-to-many. This method is called by the base class.
        """
        raise ImmutableChildWithForeignKeyException(
            'Foreign key found on model %s. Foreign keys cannot be used '\
            'on Immutable models.' % Child)

    def to_struct(self):
        """Override base model to include an ID verification.
        """
        struct = super(ImmutableModel, self).to_struct()
        self._verify_unique_id(struct)
        return struct

    def _verify_unique_id(self, struct):
        """Verify that model contents match the model ID, which is a hash of 
        the contents.
        """
        if not self._calculate_unique_id(struct) == self._id:
            raise UniqueIdMismatchError(
                "The _id %s is out of sync with the hash of contents %s "\
                "on model %s" %(self._id, struct, self.__class__))

    class Meta:
        abstract = True
