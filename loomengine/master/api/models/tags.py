from django.db import models
from django.utils import timezone

from .base import BaseModel
from api.exceptions import ConcurrentModificationError
from api.models import validators

TAG_TYPES=(
    ('file', 'File'),
    ('template', 'Template'),
    ('run', 'Run'),
)

class Tag(BaseModel):
    """A Tag may be applied to a file, template, or run. Tags may be added or
    deleted without changing the object. Tags cannot be imported or exported.
    Each tag name must be unique. Tags cannot be edited, only created and deleted.
    """
    name = models.CharField(max_length=255, unique=True)
    type = models.CharField(
        max_length=16,
        choices=TAG_TYPES)

    datetime_created = models.DateTimeField(default=timezone.now,
                                            editable=False)
    file = models.ForeignKey('DataObject',
                            related_name='tags',
                            on_delete=models.CASCADE,
                            null=True,
                            blank=True)
    template = models.ForeignKey('Template',
                            related_name='tags',
                            on_delete=models.CASCADE,
                            null=True,
                            blank=True)
    run = models.ForeignKey('Run',
                            related_name='tags',
                            on_delete=models.CASCADE,
                            null=True,
                            blank=True)

    def target(self):
        # dummy method because serializer complains if it doesn't exist
        pass

    def clean(self):
        validators.validate_tag(self)
