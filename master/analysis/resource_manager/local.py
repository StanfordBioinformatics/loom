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


class LocalResourceManager:

    @classmethod
    def run(cls, step_run):
        cmd = '%s --run_id %s --master_url %s --file_server %s --file_root %s' % (
            STEP_RUNNER_EXECUTABLE,
            step_run._id,
            settings.MASTER_URL,
            settings.LOCAL_FILE_SERVER,
            settings.FILE_ROOT,
            )
        logger.debug(cmd)

        proc = subprocess.Popen(cmd, shell=True)

        #TODO save proc.pid for follow-up
