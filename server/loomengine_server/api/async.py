from __future__ import absolute_import, unicode_literals
from celery import shared_task
from celery.decorators import periodic_task
import copy
from datetime import datetime, timedelta
from django import db
from django.utils import timezone
import logging
from api import get_setting
import os
import pytz
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
def _postprocess_run(run_uuid):
    from api.models import Run
    Run.postprocess(run_uuid)

def postprocess_run(*args, **kwargs):
    if get_setting('TEST_NO_POSTPROCESS'):
        logger.debug('Skipping async._postprocess_run because '\
                     'TEST_NO_POSTPROCESS is True')
        return
    return _run_with_delay(_postprocess_run, args, kwargs)

@shared_task
def _run_task(task_uuid, delay=0):
    time.sleep(delay)
    # If task has been run before, old TaskAttempt will be rendered inactive
    from api.models.tasks import Task
    task = Task.objects.get(uuid=task_uuid)
    # Do not run again if already running
    if task.task_attempt and not task.is_unresponsive():
        return
    task_attempt = task.create_and_activate_attempt()
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
    if polling_interval > heartbeat_interval:
        raise Exception(
            'TASKRUNNER_HEARTBEAT_INTERVAL_SECONDS cannot be less than '\
            'polling interval "%s"' % polling_interval)

    t = threading.Thread(target=function, args=args, kwargs=kwargs)
    t.start()

    last_heartbeat = task_attempt.last_heartbeat

    while t.is_alive():
        # Beat if (heartbeat_interval - polling_interval) has elapsed,
        # to ensure that we never exceed heartbeat_interval between beats.
        if (datetime.utcnow().replace(tzinfo=pytz.utc) - last_heartbeat)\
           .total_seconds() > (heartbeat_interval - polling_interval):
            last_heartbeat = task_attempt.heartbeat()
        time.sleep(polling_interval)

def _run_execute_task_attempt_playbook(task_attempt):
    from django.contrib.auth.models import User
    from django.db import IntegrityError
    from rest_framework.authtoken.models import Token

    if get_setting('LOGIN_REQUIRED'):
        try:
            loom_user = User.objects.create(username='loom-system')
        except IntegrityError:
            loom_user = User.objects.get(username='loom-system')
        try:
            token = Token.objects.get(user=loom_user).key
        except Token.DoesNotExist:
            token = Token.objects.create(user=loom_user).key
    else:
        token = None

    env = copy.copy(os.environ)
    playbook = os.path.join(
        get_setting('PLAYBOOK_PATH'),
        get_setting('RUN_TASK_ATTEMPT_PLAYBOOK'))
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
        disk_size = str(resources.get('disk_size', ''))
        cores = str(resources.get('cores', ''))
        memory = str(resources.get('memory', ''))
    else:
        disk_size = ''
        cores = ''
        memory = ''
    docker_image = task_attempt.task.run.template.environment.get(
        'docker_image')
    name = task_attempt.task.run.name

    new_vars = {'LOOM_TASK_ATTEMPT_ID': str(task_attempt.uuid),
                'LOOM_TASK_ATTEMPT_DOCKER_IMAGE': docker_image,
                'LOOM_TASK_ATTEMPT_STEP_NAME': name,
    }
    if token:
        new_vars['LOOM_TOKEN'] = token
    if cores:
        new_vars['LOOM_TASK_ATTEMPT_CORES'] = cores
    if disk_size:
        new_vars['LOOM_TASK_ATTEMPT_DISK_SIZE_GB'] = disk_size
    if memory:
        new_vars['LOOM_TASK_ATTEMPT_MEMORY'] = memory

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
        logger.error('async._run_execute_task_attempt_playbook failed for '\
                     'task_attempt.uuid="%s" with returncode="%s".'
                     % (task_attempt.uuid, p.returncode))
        msg = "Failed to launch worker process for TaskAttempt %s" \
              % task_attempt.uuid
        task_attempt.add_event(msg,
                               detail=terminal_output,
                               is_error=True)
        task_attempt.fail(detail="Failed to launch worker process")

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
        get_setting('CLEANUP_TASK_ATTEMPT_PLAYBOOK'))
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

    p = subprocess.Popen(
        cmd_list, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    terminal_output, err_is_empty = p.communicate()
    if p.returncode != 0:
        msg = 'Cleanup failed for task_attempt.uuid="%s" with returncode="%s".' % (
            task_attempt.uuid, p.returncode)
        logger.error(msg)
        task_attempt.add_event(msg,
                               detail=terminal_output,
                               is_error=True)
        raise Exception(msg)

@shared_task
def _finish_task_attempt(task_attempt_uuid):
    from api.models.tasks import TaskAttempt
    task_attempt = TaskAttempt.objects.get(uuid=task_attempt_uuid)
    task_attempt.finish()

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
        raise

def kill_task_attempt(*args, **kwargs):
    return _run_with_delay(_kill_task_attempt, args, kwargs)

@shared_task
def _send_run_notifications(run_uuid):
    from api.models.runs import Run
    run = Run.objects.get(uuid=run_uuid)
    run.send_notifications()

def send_run_notifications(*args, **kwargs):
    return _run_with_delay(_send_run_notifications, args, kwargs)

SYSTEM_CHECK_INTERVAL_MINUTES = get_setting('SYSTEM_CHECK_INTERVAL_MINUTES')

@periodic_task(run_every=timedelta(minutes=SYSTEM_CHECK_INTERVAL_MINUTES))
def check_for_stalled_tasks():
    """Check for tasks that are no longer sending a heartbeat
    """
    from api.models.tasks import Task
    for task in Task.objects.filter(status_is_running=True):
        if task.is_unresponsive():
            task.system_error()

@periodic_task(run_every=timedelta(minutes=SYSTEM_CHECK_INTERVAL_MINUTES))
def check_for_missed_cleanup():
    """Check for TaskAttempts that were never cleaned up
    """
    if get_setting('PRESERVE_ALL'):
        return
    from api.models.tasks import TaskAttempt
    if get_setting('PRESERVE_ON_FAILURE'):
        for task_attempt in TaskAttempt.objects.filter(
                status_is_running=False).filter(
                    status_is_cleaned_up=False).exclude(
                        status_is_failed=True):
            task_attempt.cleanup()
    else:
        for task_attempt in TaskAttempt.objects.filter(
                status_is_running=False).filter(status_is_cleaned_up=False):
            task_attempt.cleanup()

@periodic_task(run_every=timedelta(hours=1))
def clear_expired_logs():
    import elasticsearch
    import curator
    elasticsearch_host = get_setting('ELASTICSEARCH_HOST')
    elasticsearch_port = get_setting('ELASTICSEARCH_PORT')
    elasticsearch_log_expiration_days = get_setting('ELASTICSEARCH_LOG_EXPIRATION_DAYS')
    client = elasticsearch.Elasticsearch([elasticsearch_host], port=elasticsearch_port)
    ilo = curator.IndexList(client)
    ilo.filter_by_regex(kind='prefix', value='logstash-')
    ilo.filter_by_age(source='name', direction='older', timestring='%Y.%m.%d',
                      unit='days', unit_count=elasticsearch_log_expiration_days)
    delete_indices = curator.DeleteIndices(ilo)
    delete_indices.do_action()
