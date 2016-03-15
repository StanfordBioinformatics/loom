from analysis.models.base import AnalysisAppInstanceModel, AnalysisAppImmutableModel
from analysis.models.data_objects import DataObject
from universalmodels import fields


"""
This module defines Workflow and its subclasses.
A workflow is a definition of analysis to be run, but where
all inputs need not be specified.
"""


class Workflow(AnalysisAppImmutableModel):
    """Each Workflow may contain many processing steps, with results from one
    step optionally feeding into another step as input.
    Workflows are ImmutableModels in order to prevent clutter. If the same workflow
    is uploaded multiple times, duplicate objects will not be created.
    """

    NAME_FIELD = 'workflow_name'

    workflow_name = fields.CharField(max_length=255)
    steps = fields.ManyToManyField('Step')
    workflow_inputs = fields.ManyToManyField('WorkflowInput')
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


class RequestedDockerEnvironment(RequestedEnvironment):

    docker_image = fields.CharField(max_length=255)


class RequestedResourceSet(AnalysisAppImmutableModel):

    memory = fields.CharField(max_length=255)
    disk_space = fields.CharField(max_length=255)
    cores = fields.IntegerField()


class WorkflowInput(AnalysisAppImmutableModel):

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
    value = fields.JSONField(null=True)


class WorkflowOutput(AnalysisAppImmutableModel):

    from_channel = fields.CharField(max_length=255)
    output_name = fields.CharField(max_length=255)


class StepInput(AnalysisAppImmutableModel):

    from_channel = fields.CharField(max_length=255)
    to_path = fields.CharField(max_length=255)


class StepOutput(AnalysisAppImmutableModel):

    from_path = fields.CharField(max_length=255)
    to_channel = fields.CharField(max_length=255)
