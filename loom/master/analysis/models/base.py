from django.core.exceptions import ObjectDoesNotExist
from django.db import models
import re

from analysis.exceptions import *
from universalmodels.models import ImmutableModel, InstanceModel


class _ModelMixin(object):
    """This class provides common functions for models:
    - a standard way to assign and access human readable
    object names for use in URLs and error messages
    - a query function for looking up objects
    """

    _class_name = None
    _class_name_plural = None

    # Used for CamelCase to underscore conversions
    first_cap_re = re.compile('(.)([A-Z][a-z]+)')
    all_cap_re = re.compile('([a-z0-9])([A-Z])')

    # To override
    NAME_FIELD = None
    
    @classmethod
    def get_class_name(cls, plural=False):
        if plural:
            return cls._get_plural_name()
        else:
            return cls._get_singular_name()

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

    @classmethod
    def get_by_abbreviated_id(cls, _id):
        MIN_LENGTH = 1
        if len(_id) < MIN_LENGTH:
            raise IdTooShortError('ID length must be at least %s' % MIN_LENGTH)
        return cls.objects.filter(_id__startswith=_id)

    @classmethod
    def get_by_name(cls, name):
        """Returns a queryset of models matching the given name
        """
        if cls.NAME_FIELD is None:
            return cls.objects.none()
        kwargs = {cls.NAME_FIELD: name}
        return cls.objects.filter(**kwargs)

    @classmethod
    def get_by_name_or_id(cls, query_string):
        if not cls._is_query_string_valid(query_string):
            return cls.objects.none()
        name, id, name_or_id = cls._parse_query_string(query_string)
        if id and (not name):
            try:
                return cls.get_by_abbreviated_id(id)
            except IdTooShortError:
                return cls.objects.none()
        elif name and (not id):
            return cls.get_by_name(name)
        elif name and id:
            models = cls.get_by_name(name)
            models2 = models.filter(_id__startswith=id)
            return models2
        elif name_or_id:
            models1 = cls.get_by_name(name_or_id)
            try:
                models2 = cls.get_by_abbreviated_id(name_or_id)
            except IdTooShortError:
                models2 = cls.objects.none()
            return models1 | models2
        else:
            return cls.objects.none()

    @classmethod
    def _is_query_string_valid(cls, query_string):
        """Matches queries of the form ID, name, name@ID, or @ID.
        """
        match = re.match(r'(^[a-zA-Z0-9_/-/.]*(@[a-fA-F0-9]+)?$)|(^@?[a-fA-F0-9]+$)', query_string)
        return bool(match)

    @classmethod
    def _parse_query_string(cls, query_string):
        if '@' not in query_string:
            name = ''
            id = ''
            name_or_id = query_string
        else:
            (name, id) = query_string.split('@')
            name_or_id = ''
        return (name, id, name_or_id)


class AnalysisAppInstanceModel(InstanceModel, _ModelMixin):

    def __unicode__(self):
        return self._id

    class Meta:
        abstract = True
        app_label = 'analysis'


class AnalysisAppImmutableModel(ImmutableModel, _ModelMixin):

    def __unicode__(self):
        return self._id

    class Meta:
        abstract = True
        app_label = 'analysis'
