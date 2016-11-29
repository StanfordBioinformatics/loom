from __future__ import absolute_import, unicode_literals
from celery import shared_task

@shared_task
def add(x, y):
    return x + y


@shared_task
def postprocess_workflow(workflow_id):
    from api.serializers.templates import WorkflowSerializer
    WorkflowSerializer.postprocess(workflow_id)


@shared_task
def postprocess_step(step_id):
    from api.serializers.templates import StepSerializer
    StepSerializer.postprocess(step_id)


