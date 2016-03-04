import logging
import os
import subprocess
import errno 

from django.conf import settings
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver

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

class CloudTaskManager:

    @classmethod
    def run(cls, step_run):

        resources = CloudTaskManager._get_resource_requirements(step_run)
        cloud_driver = CloudTaskManager._get_cloud_driver()

    	CloudTaskManager._create_file_root_on_worker()

        # Construct command to run on worker node
        cmd = '%s %s --run_id %s --master_url %s' % (
            PYTHON_EXECUTABLE,
            STEP_RUNNER_EXECUTABLE,
            step_run._id,
            settings.MASTER_URL_FOR_WORKER,
            )
        if step_run.steps.count() == 0:
            raise Exception("No Step found for StepRun %s" % step_run._id)

        # Use Slurm to call the step runner on a worker node
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
    
    @classmethod
    def _get_resource_requirements(cls, step_run):
        # Retrieve resource requirements
        # If step_run has more than one step, requirements
        # should be identical in all steps.
        resources = None
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
        return resources

    @classmethod
    def _get_cloud_driver(cls):
        if settings.MASTER_TYPE == 'GOOGLE_CLOUD': #TODO: support other cloud providers
            provider = Provider.GCE 
            args = ['','']  # assumed to be running in GCE; get credentials from metadata service
                            # (see http://libcloud.readthedocs.org/en/latest/compute/drivers/gce.html#using-gce-internal-authorization)
            kwargs = {'project': settings.PROJECT_ID}
        else: 
            raise CloudTaskManagerError('Not a recognized cloud provider: ' + settings.MASTER_TYPE)
        driver_factory = get_driver(provider)
        driver = driver_factory(*args, **kwargs)
        return driver

    @classmethod
    def _create_file_root_on_worker(cls):
        try:
            os.makedirs(settings.FILE_ROOT_FOR_WORKER)
        except OSError as e:
            if e.errno == errno.EEXIST and os.path.isdir(settings.FILE_ROOT_FOR_WORKER):
                pass
            else:
                raise


class CloudTaskManagerError(Exception):
    pass
