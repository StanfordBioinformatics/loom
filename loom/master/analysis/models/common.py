from django.db import models
import re

from universalmodels.models import ImmutableModel, InstanceModel


class _ClassNameMixin(object):
    """Base class provides a standard way to assign and access human readable
    object names for use in URLs and error messages.
    """

    _class_name = None
    _class_name_plural = None

    # Used for CamelCase to underscore conversions
    first_cap_re = re.compile('(.)([A-Z][a-z]+)')
    all_cap_re = re.compile('([a-z0-9])([A-Z])')

    @classmethod
    def get_name(cls, plural=False):
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
    
class AnalysisAppInstanceModel(InstanceModel, _ClassNameMixin):

    def __unicode__(self):
        return self._id
                
    class Meta:
        abstract = True
        app_label = 'analysis'


class AnalysisAppImmutableModel(ImmutableModel, _ClassNameMixin):

    def __unicode__(self):
        return self._id
                
    class Meta:
        abstract = True
        app_label = 'analysis'

