from django.core.exceptions import ValidationError, ObjectDoesNotExist

from .common import AnalysisAppInstanceModel
from .data_objects import AbstractDataObject
from universalmodels import fields


"""
This module contains WorkflowRunRequest and other classes related to
receiving a request for analysis from a user.
"""

class WorkflowRunRequest(AnalysisAppInstanceModel):
    """Each WorkflowRunRequest may contain many processing steps, with results from one
    step optionally feeding into another step as input.
    """

    step_run_requests = fields.OneToManyField('StepRunRequest', related_name='workflow_run_request')
    inputs = fields.OneToManyField('WorkflowRunRequestInput', related_name='workflow_run_request')
    outputs = fields.OneToManyField('WorkflowRunRequestOutput', related_name='workflow_run_request')
    
    force_rerun = fields.BooleanField(default=False)
    
    is_running = fields.BooleanField(default=False)
    is_complete = fields.BooleanField(default=False)
    has_error = fields.BooleanField(default=False)

    @classmethod
    def order_by_most_recent(cls, count=None):
        workflow_run_requests = cls.objects.order_by('datetime_created').reverse()
        if count is not None and (workflow_run_requests.count() > count):
            return workflow_run_requests[:count]
        else:
            return workflow_run_requests


class StepRunRequest(AnalysisAppInstanceModel):
    """A StepRunRequest is the template for a task to be run. Typically a StepRunRequest will spawn one 
    StepRun, but if the step receives array input(s) it can spawn many parallel StepRuns. Alternatively,
    if the StepRunRequest matches previous runs, it may use old results and spawn no new StepRuns.
    """

    name = fields.CharField(max_length=255)
    command = fields.CharField(max_length=255)
    interpreter = fields.CharField(max_length=255)
    constants = fields.JSONField(null=True)
    environment = fields.OneToOneField('RequestedEnvironment')
    resources = fields.OneToOneField('RequestedResourceSet')
    
    step_run_request_inputs = fields.OneToManyField('StepRunRequestInput')
    step_run_request_outputs = fields.OneToManyField('StepRunRequestOutput')

    is_complete = fields.BooleanField(default=False)
    is_running = fields.BooleanField(default=False)
    has_error = fields.BooleanField(default=False)


class RequestedEnvironment(AnalysisAppInstanceModel):

    pass


class RequestedDockerImage(RequestedEnvironment):

    docker_image = fields.CharField(max_length = 255)


class RequestedResourceSet(AnalysisAppInstanceModel):

    memory = fields.CharField(max_length = 255)
    disk_space = fields.CharField(max_length = 255)
    cores = fields.IntegerField()

    
class WorkflowRunRequestInput(AnalysisAppInstanceModel):

    data_object = fields.OneToOneField(AbstractDataObject)
    from_path = fields.CharField(max_length = 255)
    to_channel = fields.CharField(max_length = 255)
    rename = fields.CharField(max_length = 255)

    
class WorkflowRunRequestOutput(AnalysisAppInstanceModel):

    from_channel = fields.CharField(max_length = 255)
    rename = fields.CharField(max_length = 255)

    
class StepRunRequestInput(AnalysisAppInstanceModel):

    from_channel = fields.CharField(max_length = 255)
    to_path = fields.CharField(max_length = 255)
    rename = fields.CharField(max_length = 255)

    
class StepRunRequestOutput(AnalysisAppInstanceModel):
    
    from_path = fields.CharField(max_length = 255)
    to_channel = fields.CharField(max_length = 255)
    rename = fields.CharField(max_length = 255)
