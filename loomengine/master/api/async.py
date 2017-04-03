from __future__ import absolute_import, unicode_literals
from celery import shared_task
from celery.decorators import periodic_task
import copy
import datetime
from django import db
from django.utils import timezone
import logging
from api import get_setting
import kombu.exceptions
import os
import subprocess
import sys
import threading
import time

from api.exceptions import ConcurrentModificationError

logger = logging.getLogger(__name__)

def _run_with_delay(task_function, args, kwargs):
    if get_setting('TEST_DISABLE_TASK_DELAY'):
        # Delay disabled, run synchronously
        return task_function(*args, **kwargs)

    db.connections.close_all()
    time.sleep(0.0001) # Release the GIL
    task_function.delay(*args, **kwargs)

@shared_task
def _postprocess_workflow(workflow_uuid):
    from api.models.templates import Workflow
    from api.serializers.templates import WorkflowSerializer

    try:
        Workflow.objects.filter(uuid=workflow_uuid)
        WorkflowSerializer.postprocess(workflow_uuid)
    except db.DatabaseError:
        # Ignore this task since the same one is already running
        pass

def postprocess_workflow(*args, **kwargs):
    if get_setting('TEST_NO_POSTPROCESS'):
        return
    return _run_with_delay(_postprocess_workflow, args, kwargs)

@shared_task
def _postprocess_step(step_uuid):
    from api.serializers.templates import StepSerializer
    StepSerializer.postprocess(step_uuid)

def postprocess_step(*args, **kwargs):
    if get_setting('TEST_NO_POSTPROCESS'):
        return
    return _run_with_delay(_postprocess_step, args, kwargs)

@shared_task
def _postprocess_step_run(run_uuid):
    from api.serializers.runs import StepRun
    StepRun.postprocess(run_uuid)

def postprocess_step_run(*args, **kwargs):
    if get_setting('TEST_NO_POSTPROCESS'):
        return
    return _run_with_delay(_postprocess_step_run, args, kwargs)

@shared_task
def _postprocess_workflow_run(run_uuid):
    from api.serializers.runs import WorkflowRun
    WorkflowRun.postprocess(run_uuid)

def postprocess_workflow_run(*args, **kwargs):
    if get_setting('TEST_NO_POSTPROCESS'):
        return
    return _run_with_delay(_postprocess_workflow_run, args, kwargs)

@shared_task
def _run_task(task_uuid):
    # If task has been run before, old TaskAttempt will be rendered inactive
    from api.models.tasks import Task
    task = Task.objects.get(uuid=task_uuid)
    task_attempt = task.create_and_activate_attempt()
    _run_with_heartbeats(task_attempt, _run_task_runner_playbook, args=[task_attempt])

def run_task(*args, **kwargs):
    return _run_with_delay(_run_task, args, kwargs)

def _run_with_heartbeats(task_attempt, function, args=None, kwargs=None):
    from api.models.tasks import TaskAttempt
    heartbeat_interval = int(get_setting('TASKRUNNER_HEARTBEAT_INTERVAL_SECONDS'))
    polling_interval = 1

    t = threading.Thread(target=function, args=args, kwargs=kwargs)
    t.start()

    last_heartbeat = datetime.datetime(datetime.MINYEAR,1,1,0,0, tzinfo=timezone.UTC())

    while t.is_alive():
        if (timezone.now() - last_heartbeat).total_seconds() > heartbeat_interval:
            save_tries_left = 3
            while save_tries_left > 0:
                try:
                    task_attempt = TaskAttempt.objects.get(uuid=task_attempt.uuid)
                    task_attempt.heartbeat()
                    break
                except ConcurrentModificationError:
                    if save_tries_left == 0:
                        logger.warn('Failed to send heartbeat for TaskAttemp %s' %
                                     task_attempt.uuid)
                        break
                save_tries_left -= 1
            last_heartbeat = timezone.now()
        time.sleep(polling_interval)

def _run_task_runner_playbook(task_attempt):
    env = copy.copy(os.environ)
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

    if get_setting('DEBUG'):
        cmd_list.append('-vvvv')

    disk_size = task_attempt.task.step_run.template.resources.get('disk_size')
    new_vars = {'LOOM_TASK_ATTEMPT_ID': str(task_attempt.uuid),
                'LOOM_TASK_ATTEMPT_CORES':
                task_attempt.task.step_run.template.resources.get('cores'),
                'LOOM_TASK_ATTEMPT_MEMORY':
                task_attempt.task.step_run.template.resources.get('memory'),
                'LOOM_TASK_ATTEMPT_DISK_SIZE_GB':
                disk_size if disk_size else '1', # guard against None value
                'LOOM_TASK_ATTEMPT_DOCKER_IMAGE':
                task_attempt.task.step_run.template.environment.get('docker_image'),
                'LOOM_TASK_ATTEMPT_STEP_NAME':
                task_attempt.task.step_run.template.name,
                }
    env.update(new_vars)

    p = subprocess.Popen(cmd_list, env=env,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    terminal_output = ''
    for line in iter(p.stdout.readline, ''):
        terminal_output += line
        print line.strip()
    p.wait()
    if p.returncode != 0:
        task_attempt.add_timepoint(
            "Failed to launch worker process for TaskAttempt %s" \
            % task_attempt.uuid,
            detail=terminal_output,
            is_error=True)
        task_attempt.fail()

@shared_task
def _cleanup_task_attempt(task_attempt_uuid):
    from api.models.tasks import TaskAttempt
    task_attempt = TaskAttempt.objects.get(uuid=task_attempt_uuid)
    _run_cleanup_task_playbook(task_attempt)

def cleanup_task_attempt(*args, **kwargs):
    return _run_with_delay(_cleanup_task_attempt, args, kwargs)

def _run_cleanup_task_playbook(task_attempt):
    env = copy.copy(os.environ)
    playbook = os.path.join(
        get_setting('PLAYBOOK_PATH'),
        get_setting('LOOM_CLEANUP_TASK_PLAYBOOK'))
    cmd_list = ['ansible-playbook',
                '-i', get_setting('ANSIBLE_INVENTORY'),
                playbook,
                # Without this, ansible uses /usr/bin/python,
                # which may be missing needed modules
                '-e', 'ansible_python_interpreter="/usr/bin/env python"',
    ]

    if get_setting('DEBUG'):
        cmd_list.append('-vvvv')

    new_vars = {'LOOM_TASK_ATTEMPT_ID': str(task_attempt.uuid),
                'LOOM_TASK_ATTEMPT_STEP_NAME':
                task_attempt.task.step_run.template.name,
                }
    env.update(new_vars)

    return subprocess.Popen(cmd_list, env=env, stderr=subprocess.STDOUT)

@shared_task
def _finish_task_attempt(task_attempt_uuid):
    from api.models.tasks import TaskAttempt
    task_attempt = TaskAttempt.objects.get(uuid=task_attempt_uuid)
    task_attempt.finish()

def finish_task_attempt(task_attempt_uuid):
    args = [task_attempt_uuid]
    kwargs = {}
    return _run_with_delay(_finish_task_attempt, args, kwargs)

