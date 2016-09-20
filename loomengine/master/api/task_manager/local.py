import logging
import os
import requests
import subprocess
import sys

from api import get_setting

logger = logging.getLogger('LoomDaemon')

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
        proc = subprocess.Popen(cmd, stderr=subprocess.STDOUT)
