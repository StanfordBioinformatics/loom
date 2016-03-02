import hashlib
import logging
import os
import requests
import subprocess
import errno 
from django.conf import settings

logger = logging.getLogger('LoomDaemon')

# Location of Python in virtualenv on worker node
PYTHON_EXECUTABLE = os.path.abspath(
    os.path.join(
        settings.BASE_DIR,
        '../../../bin/python',
        ))

# Location of step runner on worker node
STEP_RUNNER_EXECUTABLE = os.path.abspath(
    os.path.join(
        settings.BASE_DIR,
        '../../worker/step_runner.py',
        ))

class ClusterTaskManager:

    @classmethod
    def _create_file_root(cls):
        try:
            os.makedirs(settings.FILE_ROOT_FOR_WORKER)
        except OSError as e:
            if e.errno == errno.EEXIST and os.path.isdir(settings.FILE_ROOT_FOR_WORKER):
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
        if step_run.steps.count() == 0:
            raise Exception("No Step found for StepRun %s" % step_run._id)
        # Retrieve resource requirements
        # If step_run has more than one step, requirements
        # should be identical in all steps.
        last_resources = None
        for step in step_run.steps.all():
            resources = step.resources
            resources_json = resources.to_json()
            if last_resources is None:
                pass
            else:
                assert resources_json == last_resources, \
                    "Steps with different resource requirements were attached"\
                    " to the same StepRun. This indicates a bug in the code and"\
                    " should be avoided when attaching a Step to an existing"\
                    " StepRun."
            last_resources = resources_json

        # Make sure sbatch is on the path
        import distutils.spawn
        if distutils.spawn.find_executable('sbatch') == None:
            raise Exception('Slurm job submission executable (sbatch) not found on path')

        # Use Slurm to call the step runner on a worker node
    	ClusterTaskManager._create_file_root()
        cmd = "sbatch -D %s -n %s --mem=%s --wrap='%s'" % (
	    settings.FILE_ROOT_FOR_WORKER,
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
