from __future__ import absolute_import, unicode_literals
from celery import shared_task
from celery.decorators import periodic_task
from datetime import timedelta
from django import db
import logging
from api import get_setting, get_storage_settings
import re
import time

from django.core.exceptions import ObjectDoesNotExist
from api.exceptions import ConcurrentModificationError


"""This module contains periodic maintenance tasks and
the async_execute helper function for running async tasks
"""

logger = logging.getLogger(__name__)

def async_execute(task_function, *args, **kwargs):
    """Run a task asynchronously
    """

    if get_setting('TEST_DISABLE_ASYNC_DELAY'):
        # Delay disabled, run synchronously
        logger.debug('Running function "%s" synchronously because '\
                     'TEST_DISABLE_ASYNC_DELAY is True'
                     % task_function.__name__)
        return task_function(*args, **kwargs)

    db.connections.close_all()
    task_function.delay(*args, **kwargs)

SYSTEM_CHECK_INTERVAL_MINUTES = get_setting('SYSTEM_CHECK_INTERVAL_MINUTES')

@periodic_task(run_every=timedelta(minutes=SYSTEM_CHECK_INTERVAL_MINUTES))
def check_for_stalled_tasks():
    """Check for tasks that are no longer sending a heartbeat
    """
    from api.models.tasks import Task
    for task in Task.objects.filter(status_is_running=True):
        if not task.is_responsive():
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
    try:
        delete_indices.do_action()
    except curator.exceptions.NoIndices:
        pass

@shared_task
def _delete_file_resource(file_resource_id):
    from api.models import FileResource
    from loomengine_utils.file_utils import File
    file_resource = FileResource.objects.get(id=file_resource_id)
    file_resource.setattrs_and_save_with_retries({'upload_status': 'deleting'})

    if not file_resource.link:
        # Replace start of URL with path inside Docker container.
        file_url = file_resource.file_url
        if file_url.startswith('file:///'):
            file_url = re.sub(
                '^'+get_setting('STORAGE_ROOT_WITH_PREFIX'),
                get_setting('INTERNAL_STORAGE_ROOT_WITH_PREFIX'),
                file_url)

        file = File(file_url, get_storage_settings(), retry=True)
        file.delete(pruneto=get_setting('INTERNAL_STORAGE_ROOT'))

    file_resource.delete()

@periodic_task(run_every=timedelta(minutes=14))
def cleanup_orphaned_file_resources():
    if get_setting('DISABLE_DELETE'):
        return

    from api.models import FileResource
    queryset = FileResource.objects.filter(data_object__isnull=True)
    count = queryset.count()
    logger.info('Periodic cleanup of unused files. %s files found.' % count)
    for file_resource in queryset.all():
        _delete_file_resource(file_resource.id)

@periodic_task(run_every=timedelta(minutes=13))
def cleanup_orphaned_task_attempts():
    if get_setting('DISABLE_DELETE'):
        return

    from api.models import TaskAttempt, DataNode
    orphaned_task_attempts = TaskAttempt.objects.filter(
        tasks=None, status_is_initializing=False)
    logger.info('Periodic cleanup of unused files. %s files found.'
                % orphaned_task_attempts.count())
    nodes_to_delete = set()
    for task_attempt in orphaned_task_attempts:
        input_data_nodes = DataNode.objects.filter(
            taskattemptinput__task_attempt__uuid=task_attempt.uuid)
        output_data_nodes = DataNode.objects.filter(
            taskattemptoutput__task_attempt__uuid=task_attempt.uuid)
        for item in input_data_nodes:
            nodes_to_delete.add(item)
        for item in output_data_nodes:
            nodes_to_delete.add(item)
        task_attempt.delete()
    for item in nodes_to_delete:
        try:
            item.delete()
        except models.ProtectedError:
            pass
