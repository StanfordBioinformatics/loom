from django.db import models
from immutable.models import ImmutableModel, MutableModel


class AnalysisAppBaseModel(models.Model):
    """Base class provides a standard way to assign and access human readable
    object names for use in URLs and error messages.
    """

    _class_name = ('unnamed_model', 'unnamed_models') # To be overridden

    @classmethod
    def get_name(cls, plural=False):
        if plural:
            return cls._class_name[1]
        else:
            return cls._class_name[0]

    class Meta:
        abstract = True
        app_label = 'analysis'
