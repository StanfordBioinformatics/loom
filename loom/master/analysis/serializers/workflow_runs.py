from .base import NestedPolymorphicModelSerializer, POLYMORPHIC_TYPE_FIELD
from analysis.models.workflow_runs import *
from analysis.serializers.channels import InputOutputNodeSerializer


class AbstractWorkflowRunSerializer(NestedPolymorphicModelSerializer):
    class Meta:
        model = AbstractWorkflowRun
        exclude = (POLYMORPHIC_TYPE_FIELD,)
        subclass_serializers = {
            'workflowrun': 'analysis.serializers.workflow_runs.WorkflowRunSerializer',
            'steprun': 'analysis.serializers.workflow_runs.StepRunSerializer',
        }

class WorkflowRunSerializer(AbstractWorkflowRunSerializer):

    class Meta:
        model = WorkflowRun
        exclude = (POLYMORPHIC_TYPE_FIELD,)
        nested_x_to_many_serializers = {
            'step_runs': 'analysis.serializers.workflow_runs.AbstractWorkflowRunSerializer',
            'inputs': 'analysis.serializers.workflow_runs.WorkflowRunInputSerializer',
            'fixed_inputs': 'analysis.serializers.workflow_runs.FixedWorkflowRunInputSerializer',
            'outputs': 'analysis.serializers.workflow_runs.WorkflowRunOutputSerializer',
        }

class StepRunSerializer(AbstractWorkflowRunSerializer):

    class Meta:
        model = StepRun
        exclude = (POLYMORPHIC_TYPE_FIELD,)
        nested_x_to_many_serializers = {
            'task_runs': 'analysis.serializers.task_runs.TaskRunSerializer',
            'inputs': 'analysis.serializers.workflow_runs.StepRunInputSerializer',
            'fixed_inputs': 'analysis.serializers.workflow_runs.FixedStepRunInputSerializer',
            'outputs': 'analysis.serializers.workflow_runs.StepRunOutputSerializer',
        }

class AbstractStepRunInputSerializer(NestedPolymorphicModelSerializer):

    class Meta:
        model = AbstractStepRunInput
        exclude = (POLYMORPHIC_TYPE_FIELD,)
        subclass_serializers = {
            'stepruninput': 'analysis.serializers.workflow_runs.StepRunInputSerialiazer',
            'fixedstepruninput': 'analysis.serializers.workflow_runs.FixedStepRunInputSerialiazer',
        }

class StepRunInputSerializer(InputOutputNodeSerializer):

    class Meta:
        model = StepRunInput
        exclude = (POLYMORPHIC_TYPE_FIELD,)

class FixedStepRunInputSerializer(InputOutputNodeSerializer):

    class Meta:
        model = FixedStepRunInput
        exclude = (POLYMORPHIC_TYPE_FIELD,)

class StepRunOutputSerializer(InputOutputNodeSerializer):

    class Meta:
        model = StepRunOutput

class WorkflowRunInputSerializer(InputOutputNodeSerializer):

    class Meta:
        model = WorkflowRunInput
    
class FixedWorkflowRunInputSerializer(InputOutputNodeSerializer):

    class Meta:
        model = FixedWorkflowRunInput

class WorkflowRunOutputSerializer(InputOutputNodeSerializer):

    class Meta:
        model = WorkflowRunOutput
