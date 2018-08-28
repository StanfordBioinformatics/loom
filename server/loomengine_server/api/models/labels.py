from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from .base import BaseModel

label_validator = RegexValidator(r'^[0-9a-zA-Z_\-]*$',
                               'Only alphanumeric characters are allowed.')

class DataLabel(BaseModel):
    label = models.CharField(max_length=255, validators=[label_validator,])
    data_object = models.ForeignKey('DataObject',
                            related_name='labels',
                            on_delete=models.CASCADE,
                            null=True,
                            blank=True)
    class Meta:
        unique_together=(('label', 'data_object'))


class TemplateLabel(BaseModel):
    label = models.CharField(max_length=255, validators=[label_validator,])
    template = models.ForeignKey('Template',
                                 related_name='labels',
                                 on_delete=models.CASCADE,
                                 null=False,
                                 blank=False)
    class Meta:
        unique_together=(('label', 'template'))


class RunLabel(BaseModel):
    label = models.CharField(max_length=255, validators=[label_validator,])
    run = models.ForeignKey('Run',
                            related_name='labels',
                            on_delete=models.CASCADE,
                            null=False,
                            blank=False)
    class Meta:
        unique_together=(('label', 'run'))
