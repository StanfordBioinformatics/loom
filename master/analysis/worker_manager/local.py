import hashlib
import logging
import os
import requests
import subprocess

from django.conf import settings

from analysis.models import StepResult


logger = logging.getLogger('xppf')

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
            settings.MASTER_URL,
            )
        logger.debug(cmd)

        proc = subprocess.Popen(cmd, shell=True)

        #TODO save proc.pid for follow-up

	#For now, return process so caller can follow up
	return proc
