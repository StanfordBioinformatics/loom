from django.db import models
import jinja2
import re

from api.exceptions import *


def render_from_template(raw_text, context):
    loader = jinja2.DictLoader({'template': raw_text})
    env = jinja2.Environment(loader=loader, undefined=jinja2.StrictUndefined)
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

    def filter_by_name_or_id_or_hash(self, query_string):
        assert self.Model.NAME_FIELD, \
            'NAME_FIELD is missing on model %s' % self.Model.__name__
        assert self.Model.HASH_FIELD, \
            'HASH_FIELD is missing on model %s' % self.Model.__name__
        
        filter_args = {}
        name, id, hash_value = self._parse_as_name_or_id_or_hash(query_string)
        if name is not None:
            filter_args[self.Model.NAME_FIELD] = name
        if hash_value is not None:
            filter_args[self.Model.HASH_FIELD+'__startswith'] = hash_value
        if id is not None:
            filter_args['uuid__startswith'] = id
        return self.Model.objects.filter(**filter_args)

    def filter_by_name_or_id(self, query_string):
        """Find objects that match the identifier of form {name}@{ID}, {name},
        or @{ID}, where ID may be truncated
        """
        assert self.Model.NAME_FIELD, \
            'NAME_FIELD is missing on model %s' % self.Model.__name__
        
        kwargs = {}
        name, id = self._parse_as_name_or_id(query_string)
        if name:
            kwargs[self.Model.NAME_FIELD] = name
        if id:
            kwargs['uuid__startswith'] = id
        return self.Model.objects.filter(**kwargs)

    def _parse_as_name_or_id_or_hash(self, query_string):
        name = None
        id = None
        hash_value = None

        # Name comes at the beginning and ends with %, @, or end of string
        name_match = re.match('^(?!%|@)(.+?)($|%|@)', query_string)
        if name_match is not None:
            name = name_match.groups()[0]
        # id starts with @ and ends with % or end of string
        id_match = re.match('^.*?@(.*?)($|%)', query_string)
        if id_match is not None:
            id = id_match.groups()[0]
        # hash starts with % and ends with @ or end of string
        hash_match = re.match('^.*?%(.*?)($|@)', query_string)
        if hash_match is not None:
            hash_value = hash_match.groups()[0]
        return name, id, hash_value

    def _parse_as_name_or_id(self, query_string):
        parts = query_string.split('@')
        name = parts[0]
        id = '@'.join(parts[1:])
        return name, id

class _FilterMixin(object):

    NAME_FIELD = None

    @classmethod
    def filter_by_name_or_id_or_hash(cls, filter_string):
        helper = FilterHelper(cls)
        return helper.filter_by_name_or_id_or_hash(filter_string)

    @classmethod
    def filter_by_name_or_id(cls, filter_string):
        helper = FilterHelper(cls)
        return helper.filter_by_name_or_id(filter_string)


class BaseModel(models.Model, _ModelNameMixin, _FilterMixin):

    class Meta:
        abstract = True
        app_label = 'api'
