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
    def run(cls, task_run):

        from api.models.task_runs import TaskRunAttempt
        task_run_attempt = TaskRunAttempt.create_from_task_run(task_run)

        cmd = [
            sys.executable,
            TASK_RUNNER_EXECUTABLE,
            '--run_attempt_id',
            task_run_attempt.id.hex,
            '--master_url',
            get_setting('MASTER_URL_FOR_WORKER'),
            '--log_level',
            get_setting('LOG_LEVEL'),
            '--log_file',
            task_run_attempt.get_worker_log_file(),
        ]
        logger.debug(cmd)

        try:
            task_run_attempt.status=task_run_attempt.STATUSES.LAUNCHING_MONITOR
            task_run_attempt.save()
            proc = subprocess.Popen(cmd, stderr=subprocess.STDOUT)
        except Exception as e:
            logger.exception('Failed to launch monitor process on worker: %s')
            task_run_attempt.add_error(
                message='Failed to launch worker monitor process',
                detail=str(e))
            task_run_attempt.status = task_run_attempt.STATUSES.FINISHED
            task_run_attempt.save()

        logger.debug('Exiting LocalTaskManager')
