from django.db import models
from jinja2 import DictLoader, Environment
from polymorphic.models import PolymorphicModel, PolymorphicManager
import re

from analysis.exceptions import *


def render_from_template(raw_text, context):
    loader = DictLoader({'template': raw_text})
    env = Environment(loader=loader)
    template = env.get_template('template')
    return template.render(**context)


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


class FilterHelper(object):

    def __init__(self, Model):
        self.Model = Model

    def filter_by_abbreviated_id(self, id):
        """Find objects that match the given ID, and allow ID to be truncated
        """
        if not id:
            raise InvalidIdError('Invalid query, no id was found')
        return self.Model.objects.filter(id__startswith=id)

    def filter_by_name(self, name):
        """Returns a queryset of models matching the given name.
        Searches for name at self.Model.NAME_FIELD of the form 
        {field1}[__{field2}[__{field3}...]]
        """
        if self.Model.NAME_FIELD is None:
            return self.Model.objects.none()
        kwargs = {self.Model.NAME_FIELD: name}
        return self.Model.objects.filter(**kwargs)

    def filter_by_name_and_abbreviated_id(self, query_string):
        """Find objects that match the given {name}@{ID}, where ID may be 
        truncated
        """
        name, id = self._parse_as_name_or_id(query_string)
        models = self.filter_by_name(name)
        return models.filter(id__startswith=id)

    def filter_by_name_or_id_or_hash(self, query_string):
        kwargs = {}
        name, id, hash_value = self._parse_as_name_or_id_or_hash(query_string)
        if name is not None:
            kwargs[self.Model.NAME_FIELD+'__startswith'] = name
        if hash_value is not None:
            kwargs[self.Model.HASH_FIELD+'__startswith'] = hash_value
        if id is not None:
            kwargs['id__startswith'] = id
        return self.Model.objects.filter(**kwargs)

    def filter_by_name_or_id(self, query_string):
        """Find objects that match the identifier of form {name}@{ID}, {name},
        or @{ID}, where ID may be truncated
        """
#        if not self._is_query_string_valid(query_string):
#            return self.Model.objects.none()
        name, id = self._parse_as_name_or_id(query_string)
        if id and not name:
            return self.filter_by_abbreviated_id(id)
        elif name and not id:
            return self.filter_by_name(name)
        elif name and id:
            return self.filter_by_name_and_abbreviated_id(query_string)
        else:
            return self.Model.objects.none()

    '''
    def _is_query_string_valid(self, query_string):
        #TODO
        """Matches queries of the form name, @ID, $hash, 
        name@ID, name$hash, $hash@ID, @ID$hash,
        name@ID$hash, or name$hash@ID
        """
        name = '[a-zA-Z0-9_/-/.]*'
        id = '(@[a-fA-F0-9]+)'
        hash = '(@[a-zA-Z0-9\+\/=]+)'
        match = re.match(
            r'(^[a-zA-Z0-9_/-/.]*(@[a-fA-F0-9]+)?$)|(^@?[a-fA-F0-9]+$)',
            query_string)
        return bool(match)
    '''

    def _parse_as_name_or_id_or_hash(self, query_string):
        name = None
        id = None
        hash_value = None

        # Name comes at the beginning and ends with $, @, or end of string
        name_match = re.match('^(?!\$|@)(.+?)($|\$|@)', query_string)
        if name_match is not None:
            name = name_match.groups()[0]
        # id starts with @ and ends with $ or end of string
        id_match = re.match('^.*?@(.*?)($|\$)', query_string)
        if id_match is not None:
            id = id_match.groups()[0]
        # hash starts with $ and ends with @ or end of string
        hash_match = re.match('^.*?\$(.*?)($|@)', query_string)
        if hash_match is not None:
            hash_value = hash_match.groups()[0]
        return name, id, hash_value

    def _parse_as_name_or_id(self, query_string):
        parts = query_string.split('@')
        name = parts[0]
        id = '@'.join(parts[1:])
        return name, id

class _FilterMixin(object):

    # This functionality logically belongs in a Manager class,
    # instead of on the Model, but custom managers conflict with
    # django-polymorphic

    NAME_FIELD = None

    @classmethod
    def filter_by_name_or_id_or_hash(cls, filter_string):
        helper = FilterHelper(cls)
        return helper.filter_by_name_or_id_or_hash(filter_string)

    @classmethod
    def filter_by_name_or_id(cls, filter_string):
        helper = FilterHelper(cls)
        return helper.filter_by_name_or_id(filter_string)

    @classmethod
    def query(cls, filter_string):
        return self.filter_by_name_or_id(query_string)


class BaseModel(models.Model, _ModelNameMixin, _FilterMixin):

    class Meta:
        abstract = True
        app_label = 'analysis'


class BasePolymorphicModel(PolymorphicModel, _ModelNameMixin, _FilterMixin):

    class Meta:
        abstract = True
        app_label = 'analysis'
