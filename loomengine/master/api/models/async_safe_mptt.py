from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from mptt.managers import TreeManager
from api.models import uuidstr


"""
django-mptt is not safe for asynchronous processes sharing a database. 
It uses an IntegerField for tree_id, but instead of using autoincrement 
it computes the next available tree_id with the TreeManager's 
_get_next_tree_id function. If two trees are created at the same time 
by different processes, this delay between calling _get_next_tree_id 
and writing the new tree to the database can result in both trees 
sharing an ID. This results in a single corrupt tree.

As a workaround, this module converts tree_id to a UUID 
to avoid accidental collisions between trees.

Some functions in mptt assume tree_id is an integer assigned in 
counting order, but for our purposes the UUID works.
"""


class AsyncSafeTreeManager(TreeManager):

    def _get_next_tree_id(self):
        return uuidstr()

class AsyncSafeMPTTModel(MPTTModel):

    objects = AsyncSafeTreeManager()
    tree_id = models.CharField(max_length=255, blank=True)

    class Meta:
        abstract = True
        app_label = 'api'
