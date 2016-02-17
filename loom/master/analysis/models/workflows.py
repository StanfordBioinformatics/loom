from django.core.exceptions import ValidationError, ObjectDoesNotExist

from .common import AnalysisAppInstanceModel
from .data_objects import AbstractDataObject
from universalmodels import fields


"""
This module defines Workflow and other classes related to
receiving a request for analysis from a user.
"""


class WorkflowRunRequest(AnalysisAppInstanceModel):
    """WorkflowRunRequest represents a request to execute a Workflow on a particular
    set of inputs
    """

    workflow = fields.ForeignKey('Workflow', related_name='workflow_run_requests')
    inputs = fields.OneToManyField('WorkflowRunRequestInput', related_name='workflow_run_request')

    @classmethod
    def order_by_most_recent(cls, count=None):
        workflow_run_requests = cls.objects.order_by('datetime_created').reverse()
        if count is not None and (workflow_run_requests.count() > count):
            return workflow_run_requests[:count]
        else:
            return workflow_run_requests


class WorkflowRunRequestInput(AnalysisAppInstanceModel):
    """WorkflowRunRequestInput serves as a binding between a DataObject and a Workflow input
    in a WorkflowRunRequest
    """

    input_name = fields.CharField(max_length=255)
    data_object = fields.ForeignKey('AbstractDataObject')


class Workflow(AnalysisAppInstanceModel):
    """Each Workflow may contain many processing steps, with results from one
    step optionally feeding into another step as input.
    """

    workflow_name = fields.CharField(max_length=255)
    steps = fields.OneToManyField('Step', related_name='workflow')
    workflow_inputs = fields.OneToManyField('AbstractWorkflowInput', related_name='workflow')
    workflow_outputs = fields.OneToManyField('WorkflowOutput', related_name='workflow')

    force_rerun = fields.BooleanField(default=False)


class Step(AnalysisAppInstanceModel):
    """Steps are smaller units of processing within a Workflow. A Step can give rise to a single process,
    or it may iterate over an array to produce many parallel processing tasks.
    """

    step_name = fields.CharField(max_length=255)
    command = fields.CharField(max_length=255)
    interpreter = fields.CharField(max_length=255)
    environment = fields.OneToOneField('RequestedEnvironment')
    resources = fields.OneToOneField('RequestedResourceSet')

    step_inputs = fields.OneToManyField('StepInput')
    step_outputs = fields.OneToManyField('StepOutput')


class RequestedEnvironment(AnalysisAppInstanceModel):

    pass


class RequestedDockerImage(RequestedEnvironment):

    docker_image = fields.CharField(max_length=255)


class RequestedResourceSet(AnalysisAppInstanceModel):

    memory = fields.CharField(max_length=255)
    disk_space = fields.CharField(max_length=255)
    cores = fields.IntegerField()


class AbstractWorkflowInput(AnalysisAppInstanceModel):

    pass


class WorkflowInput(AbstractWorkflowInput):

    data_object = fields.ForeignKey(AbstractDataObject)
    to_channel = fields.CharField(max_length=255)


class WorkflowInputPlaceholder(AbstractWorkflowInput):

    input_name = fields.CharField(max_length=255)
    to_channel = fields.CharField(max_length=255)


class WorkflowOutput(AnalysisAppInstanceModel):

    from_channel = fields.CharField(max_length=255)
    rename = fields.CharField(max_length=255)


class StepInput(AnalysisAppInstanceModel):

    from_channel = fields.CharField(max_length=255)
    to_path = fields.CharField(max_length=255)
    rename = fields.CharField(max_length=255)


class StepOutput(AnalysisAppInstanceModel):

    from_path = fields.CharField(max_length=255)
    to_channel = fields.CharField(max_length=255)
    rename = fields.CharField(max_length=255)
