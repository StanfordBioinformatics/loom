from django import db
import multiprocessing
from api import get_setting
# TODO convert to asynchronous tasks with celery


def _postprocess_workflow(workflow_id):
    from api.serializers.templates import WorkflowSerializer
    WorkflowSerializer.postprocess(workflow_id)

def postprocess_workflow(*args, **kwargs):
    if get_setting('DEBUG_DISABLE_TASK_DELAY'):
        _postprocess_workflow(*args, **kwargs)
        return

    # Kill connections so new process will create its own
    db.connections.close_all()
    process = multiprocessing.Process(
        target=_postprocess_workflow,
        args=args, 
        kwargs=kwargs)
    process.start()

def _postprocess_step(step_id):
    from api.serializers.templates import StepSerializer
    StepSerializer.postprocess(step_id)

def postprocess_step(*args, **kwargs):
    if get_setting('DEBUG_DISABLE_TASK_DELAY'):
        _postprocess_step(*args, **kwargs)
        return

    # Kill connections so new process will create its own
    db.connections.close_all()
    process = multiprocessing.Process(
        target=_postprocess_step,
        args=args, 
        kwargs=kwargs)
    process.start()

def _postprocess_step_run(run_id):
    from api.serializers.runs import StepRun
    StepRun.postprocess(run_id)

def postprocess_step_run(*args, **kwargs):
    if get_setting('DEBUG_DISABLE_TASK_DELAY'):
        _postprocess_step_run(*args, **kwargs)
        return

    # Kill connections so new process will create its own
    db.connections.close_all()
    process = multiprocessing.Process(
        target=_postprocess_step_run,
        args=args, 
        kwargs=kwargs)
    process.start()

def _postprocess_workflow_run(run_id):
    from api.serializers.runs import WorkflowRun
    WorkflowRun.postprocess(run_id)

def postprocess_workflow_run(*args, **kwargs):
    if get_setting('DEBUG_DISABLE_TASK_DELAY'):
        _postprocess_workflow_run(*args, **kwargs)
        return

    # Kill connections so new process will create its own
    db.connections.close_all()
    process = multiprocessing.Process(
        target=_postprocess_workflow_run,
        args=args, 
        kwargs=kwargs)
    process.start()

def _run_step_if_ready(step_run_id):
    print "RUNNING STEP IF READY %s" % step_run_id
    from api.models import StepRun
    StepRun.run_if_ready(step_run_id)

def run_step_if_ready(*args, **kwargs):
    if get_setting('DEBUG_DISABLE_TASK_DELAY'):
        _run_step_if_ready(*args, **kwargs)
        return

    # Kill connections so new process will create its own
    db.connections.close_all()
    process = multiprocessing.Process(
        target=_run_step_if_ready,
        args=args, 
        kwargs=kwargs)
    process.start()
