from django import db
import multiprocessing
# TODO convert to asynchronous tasks with celery


def _postprocess_workflow(workflow_id):
    from api.serializers.templates import WorkflowSerializer
    WorkflowSerializer.postprocess(workflow_id)

def postprocess_workflow(*args, **kwargs):
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
    # Kill connections so new process will create its own
    db.connections.close_all()
    process = multiprocessing.Process(
        target=_postprocess_step,
        args=args, 
        kwargs=kwargs)
    process.start()

