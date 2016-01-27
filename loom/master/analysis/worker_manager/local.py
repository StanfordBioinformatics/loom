import hashlib
import logging
import os
import requests
import subprocess

from django.conf import settings


logger = logging.getLogger('LoomDaemon')

STEP_RUNNER_EXECUTABLE = os.path.abspath(
    os.path.join(
        settings.BASE_DIR,
        '../../worker/step_runner.py',
        ))


class LocalWorkerManager:

    @classmethod
    def run(cls, step_run):
        cmd = '%s --run_id %s --master_url %s' % (
            STEP_RUNNER_EXECUTABLE,
            step_run._id,
            settings.MASTER_URL_FOR_WORKER,
            )
        logger.debug(cmd)
        print cmd
        proc = subprocess.Popen(cmd, shell=True)
        step_run.update({'is_running': True})
        # TODO save proc.pid for follow-up
	# For now, return process so caller can follow up
	return proc
