from django.db import models
from django.utils import timezone
from mptt.models import MPTTModel, TreeForeignKey
from .base import BaseModel
from api.models import uuidstr


class Process(MPTTModel, BaseModel):
    """ A Process represents an executing event. It is a concrete superclass of
    Runs, Tasks, and TaskAttempts. Process contains fields useful in summarizing
    the current state of executing events, such as status and datetime_created.

    Processes can each have one parent Process, and multiple child Processes.
    This tree structure is stored and traversed using django-mptt in order to
    minimize the number of queries needed to retrieve Process subtrees.
    """
    process_parent = TreeForeignKey('self', null=True, blank=True, related_name='process_children', db_index=True)

    class MPTTMeta:
        parent_attr = 'process_parent'

    def set_process_parent(self, parent):
        """ Sets this Process's parent, which must also be a Process or subclass
        of Process. This should be called when an instance of a subclass is
        created, in order to add the newly created object to the MPTT tree.
        """
        Process.objects.get(id=self.id).process_parent = Process.objects.get(id=parent.id)

    uuid = models.CharField(default=uuidstr, editable=False,
                            unique=True, max_length=255)
    name = models.CharField(max_length=255)

    datetime_created = models.DateTimeField(default=timezone.now,
                                            editable=False)
    datetime_finished = models.DateTimeField(null=True, blank=True)

    # While status_is_running, Loom will continue trying to complete the task
    status_is_running = models.BooleanField(default=False)
    status_is_finished = models.BooleanField(default=False)
    status_is_failed = models.BooleanField(default=False)
    status_is_killed = models.BooleanField(default=False)
    status_is_cleaned_up = models.BooleanField(default=False)
    status_is_waiting = models.BooleanField(default=True)


    @property
    def status(self):
        if self.status_is_failed:
            return 'Failed'
        elif self.status_is_killed:
            return 'Killed'
        elif self.status_is_running:
            return 'Running'
        elif self.status_is_finished:
            return 'Finished'
        elif self.status_is_cleaned_up:
            return 'Cleaned up'
        elif self.status_is_waiting:
            return 'Waiting'
        else:
            return 'Unknown'
