from django.db import models
from django.utils import timezone

from .base import BaseModel


class DataTag(BaseModel):
    tag = models.CharField(max_length=255, unique=True)
    data_object = models.ForeignKey('DataObject',
                            related_name='tags',
                            on_delete=models.CASCADE,
                            null=True,
                            blank=True)


class TemplateTag(BaseModel):
    tag = models.CharField(max_length=255, unique=True)
    template = models.ForeignKey('Template',
                                 related_name='tags',
                                 on_delete=models.CASCADE,
                                 null=False,
                                 blank=False)


class RunTag(BaseModel):
    tag = models.CharField(max_length=255, unique=True)
    run = models.ForeignKey('Run',
                            related_name='tags',
                            on_delete=models.CASCADE,
                            null=False,
                            blank=False)
