from analysis.models.base import AnalysisAppInstanceModel, AnalysisAppImmutableModel
from analysis.models.data_objects import DataObject
from universalmodels import fields


"""
This module defines Workflow and its children.
A Workflow is a template of an analysis to run, where
some inputs may not be specified until runtime.
"""


class AbstractWorkflow(AnalysisAppImmutableModel):
    """An AbstractWorkflow is either a step or a collection of steps.
    Workflows are ImmutableModels in order to prevent clutter. If the same workflow 
    or step is uploaded multiple times, duplicate objects will not be created.
    """

    name = fields.CharField(max_length=255)

class Workflow(AbstractWorkflow):
    """A collection of steps or workflows
    """

    steps = fields.ManyToManyField('AbstractWorkflow', related_name='parent_workflow')
    inputs = fields.ManyToManyField('WorkflowRuntimeInput')
    fixed_inputs = fields.ManyToManyField('WorkflowFixedInput')
    outputs = fields.ManyToManyField('WorkflowOutput')


class Step(AbstractWorkflow):
    """Steps are smaller units of processing within a Workflow. A Step can give rise to a single process,
    or it may iterate over an array to produce many parallel processing tasks.
    """

    command = fields.CharField(max_length=255)
    environment = fields.ForeignKey('RequestedEnvironment')
    resources = fields.ForeignKey('RequestedResourceSet')
    inputs = fields.ManyToManyField('StepRuntimeInput')
    fixed_inputs = fields.ManyToManyField('StepFixedInput')
    outputs = fields.ManyToManyField('StepOutput')


class RequestedEnvironment(AnalysisAppImmutableModel):

    pass


class RequestedDockerEnvironment(RequestedEnvironment):

    docker_image = fields.CharField(max_length=255)


class RequestedResourceSet(AnalysisAppImmutableModel):

    memory = fields.CharField(max_length=255)
    disk_space = fields.CharField(max_length=255)
    cores = fields.IntegerField()


class AbstractFixedInput(AnalysisAppImmutableModel):

    id = fields.CharField(max_length=255)
    type = fields.CharField(
        max_length=255,
        choices=(
            ('file', 'File'),
            # ('file_array', 'File Array'),
            # ('boolean', 'Boolean'),
            # ('boolean_array', 'Boolean Array'),
            # ('string', 'String'),
            # ('string_array', 'String Array'),
            # ('integer', 'Integer'),
            # ('integer_array', 'Integer Array'),
            # ('float', 'Float'),
            # ('float_array', 'Float Array'),
            # ('json', 'JSON'),
            # ('json_array', 'JSON Array')
        )
    )
    channel = fields.CharField(max_length=255)
    
    class Meta:
        abstract = True

class AbstractRuntimeInput(AnalysisAppImmutableModel):

    hint = fields.CharField(max_length=255, null=True)
    type = fields.CharField(
        max_length=255,
        choices=(
            ('file', 'File'),
            # ('file_array', 'File Array'),
            # ('boolean', 'Boolean'),
            # ('boolean_array', 'Boolean Array'),
            # ('string', 'String'),
            # ('string_array', 'String Array'),
            # ('integer', 'Integer'),
            # ('integer_array', 'Integer Array'),
            # ('float', 'Float'),
            # ('float_array', 'Float Array'),
            # ('json', 'JSON'),
            # ('json_array', 'JSON Array')
        )
    )
    channel = fields.CharField(max_length=255)

    class Meta:
        abstract = True

        
class WorkflowFixedInput(AbstractFixedInput):

    pass


class WorkflowRuntimeInput(AbstractRuntimeInput):

    pass


class StepFixedInput(AbstractFixedInput):

    pass


class StepRuntimeInput(AbstractRuntimeInput):

    pass


class AbstractOutput(AnalysisAppImmutableModel):

    channel = fields.CharField(max_length=255)
    type = fields.CharField(
        max_length=255,
        choices=(
            ('file', 'File'),
            # ('file_array', 'File Array'),
            # ('boolean', 'Boolean'),
            # ('boolean_array', 'Boolean Array'),
            # ('string', 'String'),
            # ('string_array', 'String Array'),
            # ('integer', 'Integer'),
            # ('integer_array', 'Integer Array'),
            # ('float', 'Float'),
            # ('float_array', 'Float Array'),
            # ('json', 'JSON'),
            # ('json_array', 'JSON Array')
        )
    )

    class Meta:
        abstract = True


class WorkflowOutput(AbstractOutput):

    pass


class StepOutput(AbstractOutput):

    filename = fields.CharField(max_length=255)

