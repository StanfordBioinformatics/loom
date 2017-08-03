from django.db import models
from django.utils import timezone

from .base import BaseModel


class DataLabel(BaseModel):
    label = models.CharField(max_length=255)
    data_object = models.ForeignKey('DataObject',
                            related_name='labels',
                            on_delete=models.CASCADE,
                            null=True,
                            blank=True)


class TemplateLabel(BaseModel):
    label = models.CharField(max_length=255)
    template = models.ForeignKey('Template',
                                 related_name='labels',
                                 on_delete=models.CASCADE,
                                 null=False,
                                 blank=False)


class RunLabel(BaseModel):
    label = models.CharField(max_length=255)
    run = models.ForeignKey('Run',
                            related_name='labels',
                            on_delete=models.CASCADE,
                            null=False,
                            blank=False)
