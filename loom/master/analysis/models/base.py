from django.db import models
from polymorphic.models import PolymorphicModel, PolymorphicManager
import re

from analysis.signals import post_create, post_update


class _ModelNameMixin(object):

    _class_name = None
    _class_name_plural = None

    # Used for CamelCase to underscore conversions
    first_cap_re = re.compile('(.)([A-Z][a-z]+)')
    all_cap_re = re.compile('([a-z0-9])([A-Z])')
    
    @classmethod
    def get_class_name(cls, plural=False, hyphen=False):
        
        if plural:
            name = cls._get_plural_name()
        else:
            name = cls._get_singular_name()
        if hyphen:
            name = name.replace('_','-')
            
        return name

    @classmethod
    def _get_singular_name(cls):
        if cls._class_name is not None:
            return cls._class_name
        else:
            return cls._camel_to_underscore(cls.__name__)
        
    @classmethod
    def _get_plural_name(cls):
        if cls._class_name_plural is not None:
            return cls._class_name_plural
        else:
            return cls._pluralize(cls._get_singular_name())

    @classmethod
    def _pluralize(cls, text):
        if text.endswith(('s', 'x')):
            return text + 'es'
        else:
            return text + 's'

    @classmethod
    def _camel_to_underscore(cls, text):
        s1 = cls.first_cap_re.sub(r'\1_\2', text)
        return cls.all_cap_re.sub(r'\1_\2', s1).lower()


class _SignalMixin(object):

    def send_post_create(self):
        post_create.send(self.__class__, instance=self)

    def send_post_update(self):
        post_update.send(self.__class__, instance=self)


class FilterHelper(object):

    def __init__(self, Model):
        self.Model = Model

    def get_by_abbreviated_id(self, loom_id):
        """Find objects that match the given ID, and allow ID to be truncated
        """
        if not loom_id:
            raise InvalidIdError('Invalid query, no loom_id was found')
        return self.Model.objects.filter(loom_id__startswith=loom_id)

    def get_by_name(self, name):
        """Returns a queryset of models matching the given name.
        Searches for name at self.Model.NAME_FIELD of the form 
        {field1}[__{field2}[__{field3}...]]
        """
        if self.Model.NAME_FIELD is None:
            return self.Model.objects.none()
        kwargs = {self.Model.NAME_FIELD: name}
        return self.Model.objects.filter(**kwargs)

    def get_by_name_and_full_id(self, query_string):
        """Find objects that match the given ID, and allow ID to be truncated.
        No truncation allowed.
        """
        name, loom_id, name_or_id = self._parse_query_string(query_string)
        models = self.get_by_name(name)
        return models.filter(loom_id=loom_id)

    def get_by_name_and_abbreviated_id(self, query_string):
        """Find objects that match the given {name}@{ID}, where ID may be truncated
        """
        name, loom_id, name_or_id = self._parse_query_string(query_string)
        models = self.get_by_name(name)
        return models.filter(loom_id__startswith=loom_id)

    def get_by_name_or_id(self, query_string):
        """Find objects that match the identifier of form {name}@{ID}, {name}, {ID}, or @{ID}, 
        where ID may be truncated
        """
        if not self._is_query_string_valid(query_string):
            return cls.objects.none()
        name, loom_id, name_or_id = self._parse_query_string(query_string)
        if loom_id and not name:
            try:
                return self.get_by_abbreviated_id(loom_id)
            except IdTooShortError:
                return self.Model.objects.none()
        elif name and not loom_id:
            return self.get_by_name(name)
        elif name and loom_id:
            return self.get_by_name_and_abbreviated_id(query_string)
        elif name_or_id:
            models1 = self.get_by_name(name_or_id)
            try:
                models2 = self.get_by_abbreviated_id(name_or_id)
            except IdTooShortError:
                models2 = self.Model.objects.none()
            return models1 | models2
        else:
            return self.Model.objects.none()

    def _is_query_string_valid(self, query_string):
        """Matches queries of the form ID, name, name@ID, or @ID.
        """
        match = re.match(r'(^[a-zA-Z0-9_/-/.]*(@[a-fA-F0-9]+)?$)|(^@?[a-fA-F0-9]+$)', query_string)
        return bool(match)

    def _parse_query_string(self, query_string):
        if '@' not in query_string:
            name = ''
            loom_id = ''
            name_or_id = query_string
        else:
            (name, loom_id) = query_string.split('@')
            name_or_id = ''
        return (name, loom_id, name_or_id)


        
class _FilterMixin(object):

    # This functionality logically belongs in a Manager class,
    # instead of on the Model, but managers do not work well
    # with django-polymorphic

    NAME_FIELD = None
    
    @classmethod
    def query_by_name_or_id(cls, query_string):
        helper = FilterHelper(cls)
        return helper.get_by_name_or_id(query_string)


class BaseModel(models.Model, _ModelNameMixin, _SignalMixin, _FilterMixin):

    class Meta:
        abstract = True
        app_label = 'analysis'


class BasePolymorphicModel(PolymorphicModel, _ModelNameMixin, _SignalMixin, _FilterMixin):

    class Meta:
        abstract = True
        app_label = 'analysis'
