from django.db import models
import json
import hashlib

class _Immutable(models.Model):

    # Models that extend _Immutable are used to represent analysis or data objects.
    # They are defined by a JSON object, and their id is a hash of that JSON.
    #
    # Using immutable objects ensures that if an object is changed, old references
    # to that object are unchanged, as they point to the original rather than to the
    # updated object.
    #
    # Using a content-addressable id allows related objects to always maintain links
    # when passed between servers. For example if identical analysis is submitted to one server
    # today and another server tomorrow, the latter run could query connected servers and discover
    # the results even if their existance was unknown to the user.
    #
    # parent/child relationships can be defined on the model but are redundant with the JSON.
    # They are needed to make look-ups fast, especially for retrieving a parent.

    _json = models.TextField(blank=False, null=False) #, TODO validators=[ValidationHelper.validate_and_parse_json])
    _id = models.TextField(primary_key=True, blank=False, null=False)

    def __init__(self, *args, **kwargs):
        super(_Immutable, self).__init__(*args, **kwargs)

    @classmethod
    def create(cls, data_json):
        data_obj = json.loads(data_json)
        o = cls(_json=data_json)
        for (key, value) in data_obj.iteritems():
            if isinstance(value, list):
                # ManyToOne relation
                pass
            elif isinstance(value, dict):
                # OneToOne relation
                related_cls = self.get_class_for_key(key)
                child = related_cls.create(value)
                setattr(o, key, child)
            else:
                setattr(o, key, value)
        o.save()

    def save(self):
        # Ensures that ID and JSON do not get out of sync.
        self._json = self._clean_json(self._json)
        self._calculate_and_set_unique_id()
        self.full_clean() #This runs validators
        super(_Immutable, self).save()

    @classmethod
    def get_by_id(cls, id):
        return cls.objects.get(_id=id)

    @classmethod
    def _clean_json(cls, dirty_data_json):
        # Validate json, remove whitespace, and sort keys
        try:
            data_obj = json.loads(dirty_data_json)
        except ValueError:
            raise ValidationError("Invalid JSON could not be parsed. %s" % dirty_data_json)
        return json.dumps(data_obj, sort_keys=True)

    def _calculate_unique_id(self):
        data_json = self._json
        return hashlib.sha256(data_json).hexdigest()

    def _calculate_and_set_unique_id(self):
        self._id = self._calculate_unique_id()

    def _validate_unique_id(self):
        if self._id != self._calculate_unique_id():
            raise ValidationError('Content hash %s does not match the contents %s', (self._id, self.get_unique_id))

    def clean(self):        
        # This method validates the model as a whole, and is called by full_clean when the object is saved.
        # If children override this, they should call it as super(ChildClass, self).clean()                                                                                                                
        self._validate_unique_id()
