from django.db import models
from polymorphic.models import PolymorphicModel
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
        

class BaseModel(models.Model, _ModelNameMixin, _SignalMixin):

    class Meta:
        abstract = True
        app_label = 'analysis'

class BasePolymorphicModel(PolymorphicModel, _ModelNameMixin, _SignalMixin):

    class Meta:
        abstract = True
        app_label = 'analysis'
