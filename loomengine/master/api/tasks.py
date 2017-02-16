from __future__ import absolute_import, unicode_literals
from celery import shared_task
from celery.decorators import periodic_task
import copy
import datetime
from django import db
import multiprocessing
from api import get_setting
import kombu.exceptions
import os
import subprocess
import sys

def _run_with_delay(task_function, args, kwargs):
    if get_setting('TEST_DISABLE_TASK_DELAY'):
        # Delay disabled, run synchronously
        return task_function(*args, **kwargs)

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
    from api.models.templates import Workflow
    from api.serializers.templates import WorkflowSerializer

    try:
        Workflow.objects.select_for_update(nowait=True).filter(id=workflow_id)
        WorkflowSerializer.postprocess(workflow_id)
    except db.DatabaseError:
        # Ignore this task since the same one is already running
        pass

def postprocess_workflow(*args, **kwargs):
    if get_setting('TEST_NO_POSTPROCESS'):
        return
    return _run_with_delay(_postprocess_workflow, args, kwargs)

@shared_task
def _postprocess_step(step_id):
    from api.serializers.templates import StepSerializer
    StepSerializer.postprocess(step_id)

def postprocess_step(*args, **kwargs):
    if get_setting('TEST_NO_POSTPROCESS'):
        return
    return _run_with_delay(_postprocess_step, args, kwargs)

@shared_task
def _postprocess_step_run(run_id):
    from api.serializers.runs import StepRun
    StepRun.postprocess(run_id)

def postprocess_step_run(*args, **kwargs):
    if get_setting('TEST_NO_POSTPROCESS'):
        return
    return _run_with_delay(_postprocess_step_run, args, kwargs)

@shared_task
def _postprocess_workflow_run(run_id):
    from api.serializers.runs import WorkflowRun
    WorkflowRun.postprocess(run_id)

def postprocess_workflow_run(*args, **kwargs):
    if get_setting('TEST_NO_POSTPROCESS'):
        return
    return _run_with_delay(_postprocess_workflow_run, args, kwargs)

@periodic_task(run_every=datetime.timedelta(seconds=10))
def process_active_step_runs():
    from api.models.runs import StepRun
    if get_setting('TEST_NO_AUTO_START_RUNS'):
        return
    for step_run in StepRun.objects.filter(status_finished=False, status_failed=False):
        args = [step_run.id]
        kwargs = {}
        _run_with_delay(_create_tasks_from_step_run, args, kwargs)

@shared_task
def _create_tasks_from_step_run(step_run_id):
    from api.models.runs import StepRun
    step_run = StepRun.objects.get(id=step_run_id)
    step_run.create_ready_tasks()

@periodic_task(run_every=datetime.timedelta(seconds=10))
def process_active_tasks():
    from api.models.tasks import Task
    if get_setting('TEST_NO_AUTO_START_RUNS'):
        return
    for task in Task.objects.filter(status='STARTING'):
        args = [task.id]
        kwargs = {}
        _run_with_delay(_run_task, args, kwargs)

@shared_task
def _run_task(task_id):
    from api.models.tasks import Task
    task = Task.objects.get(id=task_id)
    print "RUNNING TASK %s" % task.id
    if not task.status == 'STARTING':
        return
    task_attempt = task.create_attempt()
    _run_task_runner_playbook(str(task_attempt.uuid))

def _run_task_runner_playbook(task_attempt_id):
    playbook = os.path.join(
        get_setting('PLAYBOOK_PATH'),
        get_setting('LOOM_RUN_TASK_PLAYBOOK'))
    cmd_list = ['ansible-playbook',
                '-i', get_setting('ANSIBLE_INVENTORY'),
                playbook,
                # Without this, ansible uses /usr/bin/python,
                # which may be missing needed modules
                '-e', 'ansible_python_interpreter="/usr/bin/env python"',
    ]
    if get_setting('SSH_PRIVATE_KEY_NAME'):
        private_key_file_path = os.path.join(
            os.path.expanduser('~/.ssh'),
            get_setting('SSH_PRIVATE_KEY_NAME'))
        cmd_list.extend(['--private-key', private_key_file_path])

    if get_setting('DEBUG'):
        cmd_list.append('-vvvv')

    return subprocess.Popen(cmd_list, env=os.environ, stderr=subprocess.STDOUT)
