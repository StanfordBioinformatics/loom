from __future__ import absolute_import, unicode_literals
from celery import shared_task
from django import db
import multiprocessing
from api import get_setting
import kombu.exceptions


@shared_task
def add(x, y):
    return x + y

def _run_with_delay(task_function, args, kwargs):
    db.connections.close_all()
    try:
        task_function.delay(*args, **kwargs)
    except kombu.exceptions.OperationalError as e:
        if e.message.startswith('[Errno 8]'):
            raise Exception(
                "Message passing service for asynchronous tasks not found. "
                "Have you configured RabbitMQ correctly?")
        else:
            raise e

@shared_task
def _postprocess_workflow(workflow_id):
    from api.serializers.templates import WorkflowSerializer
    WorkflowSerializer.postprocess(workflow_id)

def postprocess_workflow(*args, **kwargs):
    if get_setting('TEST_NO_POSTPROCESS'):
        return

    if get_setting('TEST_DISABLE_TASK_DELAY'):
        _postprocess_workflow(*args, **kwargs)
        return

    _run_with_delay(_postprocess_workflow, args, kwargs)

@shared_task
def _postprocess_step(step_id):
    from api.serializers.templates import StepSerializer
    StepSerializer.postprocess(step_id)

def postprocess_step(*args, **kwargs):
    if get_setting('TEST_NO_POSTPROCESS'):
        return

    if get_setting('TEST_DISABLE_TASK_DELAY'):
        _postprocess_step(*args, **kwargs)
        return

    _run_with_delay(_postprocess_step, args, kwargs)

@shared_task
def _postprocess_step_run(run_id):
    from api.serializers.runs import StepRun
    StepRun.postprocess(run_id)

def postprocess_step_run(*args, **kwargs):
    if get_setting('TEST_NO_POSTPROCESS'):
        return

    if get_setting('TEST_DISABLE_TASK_DELAY'):
        _postprocess_step_run(*args, **kwargs)
        return

    _run_with_delay(_postprocess_step_run, args, kwargs)

@shared_task
def _postprocess_workflow_run(run_id):
    from api.serializers.runs import WorkflowRun
    WorkflowRun.postprocess(run_id)

def postprocess_workflow_run(*args, **kwargs):
    if get_setting('TEST_NO_POSTPROCESS'):
        return

    if get_setting('TEST_DISABLE_TASK_DELAY'):
        _postprocess_workflow_run(*args, **kwargs)
        return

    _run_with_delay(_postprocess_workflow_run, args, kwargs)

@shared_task
def _run_step_if_ready(step_run_id):
    from api.models import StepRun
    StepRun.run_if_ready(step_run_id)

def run_step_if_ready(*args, **kwargs):
    if get_setting('TEST_NO_AUTO_START_RUNS'):
        return

    if get_setting('TEST_DISABLE_TASK_DELAY'):
        _run_step_if_ready(*args, **kwargs)
        return

    _run_with_delay(_run_step_if_ready, args, kwargs)
