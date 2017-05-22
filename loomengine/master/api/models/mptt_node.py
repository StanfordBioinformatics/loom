from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from .base import BaseModel

class MPTTNode(MPTTModel, BaseModel):
    mptt_parent = TreeForeignKey('self', null=True, blank=True, related_name='mptt_children', db_index=True)

    class MPTTMeta:
        parent_attr = 'mptt_parent'

    def set_mptt_parent(self, parent):
        MPTTNode.objects.get(id=self.id).mptt_parent = MPTTNode.objects.get(id=parent.id)
