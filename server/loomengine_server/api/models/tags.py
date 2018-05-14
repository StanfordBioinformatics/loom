from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
import re

from .base import BaseModel

tag_validator = RegexValidator(r'^[0-9a-zA-Z_\-]*$',
                               message='Only alphanumeric characters are allowed.')

class DataTag(BaseModel):
    tag = models.CharField(max_length=255, unique=True, validators=[tag_validator,])
    data_object = models.ForeignKey('DataObject',
                            related_name='tags',
                            on_delete=models.CASCADE,
                            null=True,
                            blank=True)


class TemplateTag(BaseModel):
    tag = models.CharField(max_length=255, unique=True, validators=[tag_validator,])
    template = models.ForeignKey('Template',
                                 related_name='tags',
                                 on_delete=models.CASCADE,
                                 null=False,
                                 blank=False)


class RunTag(BaseModel):
    tag = models.CharField(max_length=255, unique=True, validators=[tag_validator,])
    run = models.ForeignKey('Run',
                            related_name='tags',
                            on_delete=models.CASCADE,
                            null=False,
                            blank=False)
