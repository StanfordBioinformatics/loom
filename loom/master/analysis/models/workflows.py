from analysis.models.base import AnalysisAppInstanceModel, AnalysisAppImmutableModel
from analysis.models.data_objects import DataObject
from universalmodels import fields


"""
This module defines Workflow and other classes related to
receiving a request for analysis from a user.
"""


class WorkflowRun(AnalysisAppInstanceModel):
    """WorkflowRun represents a request to execute a Workflow on a particular
    set of inputs
    """

    workflow = fields.ForeignKey('Workflow')
    inputs = fields.OneToManyField('WorkflowRunInput')

    @classmethod
    def order_by_most_recent(cls, count=None):
        workflow_runs = cls.objects.order_by('datetime_created').reverse()
        if count is not None and (workflow_runs.count() > count):
            return workflow_runs[:count]
        else:
            return workflow_runs


class WorkflowRunInput(AnalysisAppInstanceModel):
    """WorkflowRunInput serves as a binding between a DataObject and a Workflow input
    in a WorkflowRun
    """

    input_name = fields.CharField(max_length=255)
    data_object = fields.ForeignKey('DataObject')


class Workflow(AnalysisAppImmutableModel):
    """Each Workflow may contain many processing steps, with results from one
    step optionally feeding into another step as input.
    Workflows are ImmutableModels in order to prevent clutter. If the same workflow
    is uploaded multiple times, duplicate objects will not be created.
    """

    NAME_FIELD = 'workflow_name'
    
    workflow_name = fields.CharField(max_length=255)
    steps = fields.ManyToManyField('Step')
    workflow_inputs = fields.ManyToManyField('AbstractWorkflowInput')
    workflow_outputs = fields.ManyToManyField('WorkflowOutput')


class Step(AnalysisAppImmutableModel):
    """Steps are smaller units of processing within a Workflow. A Step can give rise to a single process,
    or it may iterate over an array to produce many parallel processing tasks.
    """

    step_name = fields.CharField(max_length=255)
    command = fields.CharField(max_length=255)
    interpreter = fields.CharField(max_length=255)
    environment = fields.ForeignKey('RequestedEnvironment')
    resources = fields.ForeignKey('RequestedResourceSet')

    step_inputs = fields.ManyToManyField('StepInput')
    step_outputs = fields.ManyToManyField('StepOutput')


class RequestedEnvironment(AnalysisAppImmutableModel):

    pass


class RequestedDockerImage(RequestedEnvironment):

    docker_image = fields.CharField(max_length=255)


class RequestedResourceSet(AnalysisAppImmutableModel):

    memory = fields.CharField(max_length=255)
    disk_space = fields.CharField(max_length=255)
    cores = fields.IntegerField()


class AbstractWorkflowInput(AnalysisAppImmutableModel):

    pass


class WorkflowInput(AbstractWorkflowInput):

    data_object = fields.ForeignKey(DataObject)
    to_channel = fields.CharField(max_length=255)


class WorkflowInputPlaceholder(AbstractWorkflowInput):

    input_name = fields.CharField(max_length=255)
    to_channel = fields.CharField(max_length=255)
    type = fields.CharField(
        max_length=255,
        choices=(
            ('file', 'File'),
            ('file_array', 'File Array'),
            ('boolean', 'Boolean'),
            ('boolean_array', 'Boolean Array'),
            ('string', 'String'),
            ('string_array', 'String Array'),
            ('integer', 'Integer'),
            ('integer_array', 'Integer Array'),
            ('float', 'Float'),
            ('float_array', 'Float Array'),
            ('json', 'JSON'),
            ('json_array', 'JSON Array')
        )
    )
    prompt = fields.CharField(max_length=255)


class WorkflowOutput(AnalysisAppImmutableModel):

    from_channel = fields.CharField(max_length=255)
    rename = fields.CharField(max_length=255)


class StepInput(AnalysisAppImmutableModel):

    from_channel = fields.CharField(max_length=255)
    to_path = fields.CharField(max_length=255)
    rename = fields.CharField(max_length=255)


class StepOutput(AnalysisAppImmutableModel):

    from_path = fields.CharField(max_length=255)
    to_channel = fields.CharField(max_length=255)
    rename = fields.CharField(max_length=255)
