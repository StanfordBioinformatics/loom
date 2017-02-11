import logging
import os
import requests
import subprocess
import sys
from django.conf import settings

from api import get_setting

logger = logging.getLogger(__name__)

TASK_RUNNER_EXECUTABLE = os.path.abspath(
    os.path.join(
        get_setting('BASE_DIR'),
        '../worker/task_runner.py',
        ))


class LocalTaskManager:

    @classmethod
    def run(cls, task):

        task_attempt = task.create_attempt()

        cmd = [
            sys.executable,
            TASK_RUNNER_EXECUTABLE,
            '--attempt_id',
            str(task_attempt.uuid),
            '--master_url',
            get_setting('MASTER_URL_FOR_WORKER'),
            '--log_level',
            get_setting('LOG_LEVEL'),
            '--log_file',
            task_attempt.get_worker_log_file(),
        ]
        logger.debug(cmd)

        try:
            task_attempt.status=task_attempt.STATUSES.LAUNCHING_MONITOR
            task_attempt.save()
            proc = subprocess.Popen(cmd, stderr=subprocess.STDOUT)
        except Exception as e:
            logger.exception('Failed to launch monitor process on worker: %s')
            task_attempt.add_error(
                message='Failed to launch worker monitor process',
                detail=str(e))
            task_attempt.status = task_attempt.STATUSES.FINISHED
            task_attempt.save()

        logger.debug('Exiting LocalTaskManager')

    @classmethod
    def delete_worker_by_task_run_attempt(cls, task_run_attempt):
        # No worker to delete
        pass
