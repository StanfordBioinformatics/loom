from __future__ import absolute_import, unicode_literals
from celery import shared_task
from celery.decorators import periodic_task
import copy
import datetime
from django import db
from django.utils import timezone
import logging
from api import get_setting
import os
import subprocess
import threading
import time

from api.exceptions import ConcurrentModificationError


"""The 'async' module contains all asynchronous methods used by api.models
"""


logger = logging.getLogger(__name__)

def _run_with_delay(task_function, args, kwargs):
    """Run a task asynchronously
    """

    if get_setting('TEST_DISABLE_ASYNC_DELAY'):
        # Delay disabled, run synchronously
        logger.debug('Running function "%s" synchronously because '\
                     'TEST_DISABLE_ASYNC_DELAY is True'
                     % task_function.__name__)
        return task_function(*args, **kwargs)

    db.connections.close_all()
    time.sleep(0.0001) # Release the GIL
    task_function.delay(*args, **kwargs)

@shared_task
def _postprocess_run(run_uuid, context):
    from api.models import Run
    Run.postprocess(run_uuid, context)

def postprocess_run(*args, **kwargs):
    if get_setting('TEST_NO_POSTPROCESS'):
        logger.debug('Skipping async._postprocess_run because '\
                     'TEST_NO_POSTPROCESS is True')
        return
    return _run_with_delay(_postprocess_run, args, kwargs)

@shared_task
def _run_task(task_uuid, context):
    # If task has been run before, old TaskAttempt will be rendered inactive
    from api.models.tasks import Task
    task = Task.objects.get(uuid=task_uuid)
    task_attempt = task.create_and_activate_attempt(context)
    if get_setting('TEST_NO_RUN_TASK_ATTEMPT'):
        logger.debug('Skipping async._run_execute_task_attempt_playbook because'\
                     'TEST_NO_RUN_TASK_ATTEMPT is True')
        return
    _run_with_heartbeats(_run_execute_task_attempt_playbook, task_attempt,
                         args=[task_attempt])

def run_task(*args, **kwargs):
    return _run_with_delay(_run_task, args, kwargs)

def _run_with_heartbeats(function, task_attempt, args=None, kwargs=None):
    from api.models.tasks import TaskAttempt
    heartbeat_interval = int(get_setting(
        'TASKRUNNER_HEARTBEAT_INTERVAL_SECONDS'))
    polling_interval = 1

    t = threading.Thread(target=function, args=args, kwargs=kwargs)
    t.start()

    last_heartbeat = datetime.datetime(datetime.MINYEAR,1,1,0,0,
                                       tzinfo=timezone.utc)
    max_retries = 5

    while t.is_alive():
        if (timezone.now() - last_heartbeat)\
           .total_seconds() > heartbeat_interval:
            retry_count = 0
            while True:
                try:
                    task_attempt = TaskAttempt.objects.get(
                        uuid=task_attempt.uuid)
                    task_attempt.heartbeat()
                    break
                except ConcurrentModificationError:
                    if retry_count >= max_retries:
                        logger.warn(
                            'Failed to send heartbeat for '\
                            'task_attempt.uuid=%s after %s retries' %
                            (task_attempt.uuid, max_retries))
                        break
                    retry_count += 1
            last_heartbeat = timezone.now()
        time.sleep(polling_interval)

def _run_execute_task_attempt_playbook(task_attempt):
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

    resources = task_attempt.task.run.template.resources
    if resources:
        disk_size = resources.get('disk_size', '')
        cores = resources.get('cores', '')
        memory = resources.get('memory', '')
    else:
        disk_size = ''
        cores = ''
        memory = ''
    docker_image = task_attempt.task.run.template.environment.get(
        'docker_image')
    name = task_attempt.task.run.name

    new_vars = {'LOOM_TASK_ATTEMPT_ID': str(task_attempt.uuid),
                'LOOM_TASK_ATTEMPT_CORES': cores,
                'LOOM_TASK_ATTEMPT_MEMORY': memory,
                'LOOM_TASK_ATTEMPT_DISK_SIZE_GB': disk_size,
                'LOOM_TASK_ATTEMPT_DOCKER_IMAGE': docker_image,
                'LOOM_TASK_ATTEMPT_STEP_NAME': name,
                }
    env.update(new_vars)

    p = subprocess.Popen(cmd_list,
                         env=env,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    terminal_output = ''
    for line in iter(p.stdout.readline, ''):
        terminal_output += line
        print line.strip()
    p.wait()
    if p.returncode != 0:
        logger.debug('async._run_execute_task_attempt_playbook failed for '\
                     'task_attempt.uuid="%s" with returncode="%s"'
                     % (task_attempt.uuid, p.returncode))
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
    task_attempt.add_event('Cleaned up',
                           is_error=False)
    task_attempt.setattrs_and_save_with_retries({
        'status_is_cleaned_up': True })

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
                task_attempt.task.run.name,
                }
    env.update(new_vars)

    return subprocess.Popen(cmd_list, env=env, stderr=subprocess.STDOUT)

@shared_task
def _finish_task_attempt(task_attempt_uuid, context):
    from api.models.tasks import TaskAttempt
    task_attempt = TaskAttempt.objects.get(uuid=task_attempt_uuid)
    task_attempt.finish(context)

def finish_task_attempt(*args, **kwargs):
    return _run_with_delay(_finish_task_attempt, args, kwargs)

@shared_task
def _kill_task_attempt(task_attempt_uuid, kill_message):
    from api.models.tasks import TaskAttempt
    task_attempt = TaskAttempt.objects.get(uuid=task_attempt_uuid)
    try:
        task_attempt.kill(kill_message)
    except Exception as e:
        logger.debug('Failed to kill task_attempt.uuid=%s.' % task_attempt_uuid)
        task_attempt.cleanup()
        raise

    task_attempt.cleanup()

def kill_task_attempt(*args, **kwargs):
    return _run_with_delay(_kill_task_attempt, args, kwargs)

@shared_task
def _send_run_notifications(run_uuid, context):
    from api.models.runs import Run
    run = Run.objects.get(uuid=run_uuid)
    run.send_notifications(context)

def send_run_notifications(*args, **kwargs):
    return _run_with_delay(_send_run_notifications, args, kwargs)
