from django.db import models
from polymorphic.models import PolymorphicModel

class BaseModel(models.Model):

    class Meta:
        abstract = True
        app_label = 'analysis'


class BasePolymorphicModel(PolymorphicModel):

    class Meta:
        abstract = True
        app_label = 'analysis'
