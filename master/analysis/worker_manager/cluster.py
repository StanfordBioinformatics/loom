import hashlib
import logging
import os
import requests
import subprocess
import errno 
from django.conf import settings

logger = logging.getLogger('XppfDaemon')

# Location of Python in virtualenv on worker node
PYTHON_EXECUTABLE = os.path.abspath(
    os.path.join(
        settings.BASE_DIR,
        '../../../env/bin/python',
        ))

# Location of step runner on worker node
STEP_RUNNER_EXECUTABLE = os.path.abspath(
    os.path.join(
        settings.BASE_DIR,
        '../../worker/step_runner.py',
        ))

class ClusterWorkerManager:

    @classmethod
    def _create_file_root(cls):
        try:
            os.makedirs(settings.FILE_ROOT)
        except OSError as e:
            if e.errno == errno.EEXIST and os.path.isdir(settings.FILE_ROOT):
                pass
            else:
                raise

    @classmethod
    def run(cls, step_run):
        cmd = '%s %s --run_id %s --master_url %s' % (
            PYTHON_EXECUTABLE,
            STEP_RUNNER_EXECUTABLE,
            step_run._id,
            settings.MASTER_URL_FOR_WORKER,
            )
        # Retrieve resource requirements 
        if step_run.step_set.count() < 1:
            raise Exception('No step found for a step run')
        if step_run.step_set.count() > 1:
            raise Exception('More than one step found for a step run')
        step = step_run.step_set.get()
        resources = step.resources

        # Make sure sbatch is on the path
        import distutils.spawn
        if distutils.spawn.find_executable('sbatch') == None:
            raise Exception('Slurm job submission executable (sbatch) not found on path')

        # Use Slurm to call the step runner on a worker node
    	ClusterWorkerManager._create_file_root()
        cmd = "sbatch -D %s -n %s --mem=%s --wrap='%s'" % (
	    settings.FILE_ROOT,
            resources.cores,
            resources.memory,
            cmd
            )

        logger.debug(cmd)

        proc = subprocess.Popen(cmd, shell=True)

        step_run.update({'is_running': True})
        #TODO save proc.pid for follow-up

	# For now, return process so caller can follow up
	# However, this is just the job submit process (sbatch), not the step runner!
	return proc
