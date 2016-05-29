from django.core.exceptions import ValidationError

from analysis.models.base import AnalysisAppInstanceModel, AnalysisAppImmutableModel
from analysis.models.data_objects import FileDataObject
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

    NAME_FIELD = 'name'
    
    name = fields.CharField(max_length=255)

    def get_input_channel_names(self):
        return [input.channel for input in self.inputs.all()]

    def get_output_channel_names(self):
        return [output.channel for output in self.outputs.all()]

    def is_step(self):
        return self.downcast().is_step()

class Workflow(AbstractWorkflow):
    """A collection of steps or workflows
    """

    steps = fields.ManyToManyField('AbstractWorkflow', related_name='parent_workflow')
    inputs = fields.ManyToManyField('WorkflowRuntimeInput')
    fixed_inputs = fields.ManyToManyField('WorkflowFixedInput')
    outputs = fields.ManyToManyField('WorkflowOutput')

    def after_create(self):
        self._validate_workflow()

    def _validate_workflow(self):
        """Make sure all channel destinations have exactly one source
        """

        source_counts = {}
        for input in self.inputs.all():
            self._increment_sources_count(source_counts, input.channel)
        for input in self.fixed_inputs.all():
            self._increment_sources_count(source_counts, input.channel)
        for step in self.steps.all():
            step = step.downcast()
            for output in step.outputs.all():
                self._increment_sources_count(source_counts, output.channel)

        for channel, count in source_counts.iteritems():
            if count > 1:
                raise ValidationError('The workflow %s@%s is invalid. It has more than one source for channel "%s". Check workflow inputs and step outputs.' % (
                    self.name,
                    self._id,
                    channel
                ))

        destinations = []
        for output in self.outputs.all():
            destinations.append(output.channel)
        for step in self.steps.all():
            step = step.downcast()
            for input in step.inputs.all():
                destinations.append(input.channel)

        sources = source_counts.keys()
        for destination in destinations:
            if not destination in sources:
                raise ValidationError('The workflow %s@%s is invalid. The channel "%s" has no source.' % (
                    self.name,
                    self._id,
                    destination
                ))

    def _increment_sources_count(self, sources, channel):
        sources.setdefault(channel, 0)
        sources[channel] += 1

    def is_step(self):
        return False

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

    def is_step(self):
        return True


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

    def _create_or_update_fields(self, data):
        matches = FileDataObject.get_by_name_and_full_id(data['id'])
        if matches.count() < 1:
            raise ValidationError('Could not find file with ID "%s"' % data['id'])
        if matches.count() > 1:
            raise ValidationError('Found multiple files with ID "%s"' % data['id'])
        o = super(AbstractFixedInput, self)._create_or_update_fields(data)
        
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

