import errno 
import json
import logging
import multiprocessing
import os
import requests
import subprocess

from django.conf import settings
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver

logger = logging.getLogger('LoomDaemon')


class CloudTaskManager:

    @classmethod
    def run(cls, step_run):

        resources = CloudTaskManager._get_resource_requirements(task_run)
        instance_type = CloudTaskManager._get_instance_type(cores=resources.cores, memory=resources.memory)

        # Don't want to block while waiting for VM to come up, so start another process to finish the rest of the steps.
        process = multiprocessing.Process(target=CloudTaskManager._create_deploy_run, args=(instance_type, cmd))
        process.start()

    @classmethod
    def _create_deploy_run(cls, instance_type, cmd):
        """Create a VM, deploy Docker and Loom, and pass command to task runner."""
        driver = CloudTaskManager._get_cloud_driver()




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
    def _get_cheapest_instance_type(cls, cores, memory):
        """ Determine the cheapest instance type given a minimum number of cores and minimum amount of RAM (in GB). """

        if settings.MASTER_TYPE != 'GOOGLE_CLOUD': #TODO: support other cloud providers
            raise CloudTaskManagerError('Not a recognized cloud provider: ' + settings.MASTER_TYPE)
        else:
            pricelist = CloudTaskManager._get_gcloud_pricelist()

            # Filter out preemptible, shared-CPU, and non-US instance types
            us_instance_types = {k:v for k,v in pricelist.items()\
                if k.startswith('CP-COMPUTEENGINE-VMIMAGE-') and not k.endswith('-PREEMPTIBLE') and 'us' in v and v['cores'] != 'shared'}

            # Convert to array and add keys (instance type names) as type names
            price_array = []
            for key in us_instance_types:
                value = us_instance_types[key] 
                value.update({'name':key.replace('CP-COMPUTEENGINE-VMIMAGE-', '').lower()})
                price_array.append(value)

            # Sort by price in US
            price_array.sort(None, lambda x: x['us'])

            # Look for an instance type that satisfies requested cores and memory; first will be cheapest
            for instance_type in price_array:
                if int(instance_type['cores']) >= int(cores) and float(instance_type['memory']) >= float(memory):
                    return instance_type['name']

            # No instance type found that can fulfill requested cores and memory
            raise CloudTaskManagerError('No instance type found with at least %d cores and %f GB of RAM.' % (cores, memory))
        
    @classmethod
    def _get_gcloud_pricelist(cls):
        """ Retrieve latest pricelist from Google Cloud, or use cached copy if not reachable. """
        try:
            r = requests.get('http://cloudpricingcalculator.appspot.com/static/data/pricelist.json')
            content = json.loads(r.content)
        except ConnectionError:
            logger.warning("Couldn't get updated pricelist from http://cloudpricingcalculator.appspot.com/static/data/pricelist.json. Falling back to cached copy, but prices may be out of date.")
            with open('pricelist.json') as infile:
                content = json.load(infile)

        logger.debug('Using pricelist ' + content['version'] + ', updated ' + content['updated'])
        pricelist = content['gcp_price_list']
        return pricelist

        
        


    @classmethod
    def _get_cloud_driver(cls):
        if settings.MASTER_TYPE != 'GOOGLE_CLOUD': #TODO: support other cloud providers
            raise CloudTaskManagerError('Not a recognized cloud provider: ' + settings.MASTER_TYPE)
        else:
            provider = Provider.GCE 
            args = ['','']  # master is running in GCE; get credentials from metadata service
                            # (more info: http://libcloud.readthedocs.org/en/latest/compute/drivers/gce.html#using-gce-internal-authorization)
            kwargs = {'project': settings.PROJECT_ID}
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

    @classmethod
    def _run_command_on_worker(cls, cmd):
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


class CloudTaskManagerError(Exception):
    pass
