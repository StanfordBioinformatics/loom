import errno 
import imp
import json
import logging
import multiprocessing
import os
import pickle
import re
import requests
import socket
import subprocess
import sys
import tempfile
from string import Template

from django.conf import settings

from loomengine.utils.connection import Connection
import loomengine.utils.version
import loomengine.utils.cloud

PLAYBOOKS_PATH = os.path.join(imp.find_module('loomengine')[1], 'playbooks')
GCLOUD_CREATE_WORKER_PLAYBOOK = os.path.join(PLAYBOOKS_PATH, 'gcloud_create_worker.yml')
GCLOUD_DELETE_WORKER_PLAYBOOK = os.path.join(PLAYBOOKS_PATH, 'gcloud_delete_worker.yml')
GCLOUD_RUN_TASK_PLAYBOOK = os.path.join(PLAYBOOKS_PATH, 'gcloud_run_task.yml')
GCE_PY_PATH = os.path.join(imp.find_module('loomengine')[1], 'utils', 'gce.py')

logger = logging.getLogger(__name__)

class CloudTaskManager:

    @classmethod
    def run(cls, task_run):
        from api.models.task_runs import TaskRunAttempt
        task_run_attempt = TaskRunAttempt.create_from_task_run(task_run)
        
        
        # Don't want to block while waiting for VM to come up, so start another process to finish the rest of the steps.
        logger.debug("Launching CloudTaskManager as a separate process.")

        requested_resources = {
            'cores': task_run_attempt.task_run.step_run.resources.cores,
            'memory': task_run_attempt.task_run.step_run.resources.memory,
            'disk_size': task_run_attempt.task_run.step_run.resources.disk_size,
        }
        environment = {
            'docker_image': task_run_attempt.task_definition.environment.docker_image,
        }
        
        hostname = socket.gethostname()
        worker_name = cls.create_worker_name(hostname, task_run_attempt)
        task_run_attempt_id = task_run_attempt.id.hex
        worker_log_file = task_run_attempt.get_worker_log_file()

        task_run_attempt.status = task_run_attempt.STATUSES.PROVISIONING_HOST
        task_run_attempt.save()

        process = multiprocessing.Process(target=CloudTaskManager._try_run, args=(task_run_attempt_id, requested_resources, environment, worker_name, worker_log_file))
        process.start()

    @classmethod
    def _try_run(cls, task_run_attempt_id, requested_resources, environment, worker_name, worker_log_file):
        try:
            cls._run(task_run_attempt_id, requested_resources, environment, worker_name, worker_log_file)
        except Exception as e:
            logger.exception('Failed to create task run attempt %s: %s' % (task_run_attempt_id, str(e)))
            
    @classmethod
    def _run(cls, task_run_attempt_id, requested_resources, environment, worker_name, worker_log_file):
        from api.models.task_runs import TaskRunAttempt

        logger.debug("CloudTaskManager separate process started.")
        logger.debug("task_run_attempt: %s" % task_run_attempt_id)

        connection = Connection(settings.MASTER_URL_FOR_SERVER)
        
        """Create a VM, deploy Docker and Loom, and pass command to task runner."""
        if settings.WORKER_TYPE != 'GOOGLE_CLOUD':
            raise CloudTaskManagerError('Unsupported cloud type: ' + settings.WORKER_TYPE)
        # TODO: Support other cloud providers. For now, assume GCE.
        instance_type = CloudTaskManager._get_cheapest_instance_type(cores=requested_resources['cores'], memory=requested_resources['memory'])
        
        scratch_disk_name = worker_name+'-disk'
        scratch_disk_device_path = '/dev/disk/by-id/google-'+scratch_disk_name
        if requested_resources.get('disk_size') is not None:
            scratch_disk_size_gb = requested_resources['disk_size']
        else:   
            scratch_disk_size_gb = settings.WORKER_SCRATCH_DISK_SIZE

        ansible_env = os.environ.copy()
        extra_env_vars = {
            'WORKER_INSTANCE_NAME': worker_name,
            'WORKER_INSTANCE_TYPE': instance_type,
            'WORKER_REMOTE_USER': 'loom',
            'WORKER_SCRATCH_DISK_DEVICE_PATH': scratch_disk_device_path,
            'WORKER_SCRATCH_DISK_NAME': scratch_disk_name,
            'WORKER_SCRATCH_DISK_SIZE': scratch_disk_size_gb,
            'TASK_RUN_ATTEMPT_ID': task_run_attempt_id,
            'TASK_RUN_DOCKER_IMAGE': environment['docker_image'],
            'WORKER_LOG_FILE': worker_log_file,
        }
        ansible_env.update(extra_env_vars)
        logger.debug('Starting worker VM using environment: %s' % ansible_env)

        try:
            with open(os.path.join(settings.LOGS_DIR, 'loom_ansible.log'), 'a', 0) as ansible_logfile:
                cls._run_playbook(GCLOUD_CREATE_WORKER_PLAYBOOK, ansible_env, logfile=ansible_logfile)
        except Exception as e:
            logger.exception('Failed to provision host.')
            connection.post_task_run_attempt_error(
                task_run_attempt_id,
                {
                    'message': 'Failed to provision host',
                    'detail': str(e)
                })
            connection.update_task_run_attempt(
                task_run_attempt_id,
                {
                    'status': TaskRunAttempt.STATUSES.FINISHED,
                })
            raise e

        try:
            with open(os.path.join(settings.LOGS_DIR, 'loom_ansible.log'), 'a', 0) as ansible_logfile:
                connection.update_task_run_attempt(
                    task_run_attempt_id,
                    {
                        'status': TaskRunAttempt.STATUSES.LAUNCHING_MONITOR,
                    })
                cls._run_playbook(GCLOUD_RUN_TASK_PLAYBOOK, ansible_env, logfile=ansible_logfile)
        except Exception as e:
            logger.exception('Failed to launch monitor process on worker: %s')
            connection.post_task_run_attempt_error(
                task_run_attempt_id,
                {
                    'message': 'Failed to launch monitor process on worker',
                    'detail': str(e)
                })
            connection.update_task_run_attempt(
                task_run_attempt_id,
                {
                    'status': TaskRunAttempt.STATUSES.FINISHED,
                })
            raise e

        logger.debug("CloudTaskManager process done.")
        ansible_logfile.close()

    @classmethod
    def _run_playbook(cls, playbook, ansible_env, logfile=None):
        """Runs a playbook. Vars are passed as env variables."""
        ansible_env['ANSIBLE_HOST_KEY_CHECKING'] = 'False'
        ansible_env['INVENTORY_IP_TYPE'] = 'internal'       # Tell gce.py to use internal IP for ansible_ssh_host
        cmd = ['ansible-playbook', '-vvv', '--key-file', os.path.expanduser(settings.GCE_SSH_KEY_FILE), '-i', GCE_PY_PATH, playbook]
        print cmd
        returncode = subprocess.call(cmd, env=ansible_env, stderr=subprocess.STDOUT, stdout=logfile)
        if not returncode == 0:
            raise Exception('Nonzero returncode %s for command: %s' % (returncode, ' '.join(cmd)))

    @classmethod
    def _get_cheapest_instance_type(cls, cores, memory):
        """Determine the cheapest instance type given a minimum number of cores and minimum amount of RAM (in GB)."""

        if settings.WORKER_TYPE != 'GOOGLE_CLOUD': #TODO: support other cloud providers
            raise CloudTaskManagerError('Not a recognized cloud provider: ' + settings.WORKER_TYPE)
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
        """Retrieve latest pricelist from Google Cloud, or use cached copy if not reachable."""
        try:
            r = requests.get('http://cloudpricingcalculator.appspot.com/static/data/pricelist.json')
            content = json.loads(r.content)
        except ConnectionError:
            logger.warning("Couldn't get updated pricelist from http://cloudpricingcalculator.appspot.com/static/data/pricelist.json. Falling back to cached copy, but prices may be out of date.")
            with open('pricelist.json') as infile:
                content = json.load(infile)

        #logger.debug('Using pricelist ' + content['version'] + ', updated ' + content['updated'])
        pricelist = content['gcp_price_list']
        return pricelist

    @classmethod
    def delete_worker_by_task_run_attempt(cls, task_run_attempt):
        """Delete the worker that ran the specified task run attempt from this server."""
        hostname = socket.gethostname()
        worker_name = cls.create_worker_name(hostname, task_run_attempt)
        cls.delete_worker_by_name(worker_name)
        
    @classmethod
    def delete_worker_by_name(cls, worker_name):
        """Delete instance with the specified name."""
        # Don't want to block while waiting for VM to be deleted, so start another process to finish the rest of the steps.
        process = multiprocessing.Process(target=CloudTaskManager._delete_worker_by_name, args=(worker_name,))
        process.start()

    @classmethod
    def _delete_worker_by_name(cls, worker_name):
        ansible_env = os.environ.copy() 
        ansible_env['WORKER_NAME'] = worker_name
        cls._run_playbook(GCLOUD_DELETE_WORKER_PLAYBOOK, ansible_env)

    @classmethod
    def create_worker_name(cls, hostname, task_run_attempt):
        """Create a name for the worker instance that will run the specified task run attempt, from this server.

        Since hostname, workflow name, and step name can easily be duplicated,
        we do this in two steps to ensure that at least 4 characters of the
        location ID are part of the name. Also, since worker scratch disks are
        named by appending '-disk' to the instance name, and disk names are max
        63 characters, leave 5 characters for the '-disk' suffix.

        """
        task_run = task_run_attempt.task_run
        #workflow_name = task_run.workflow_name
        step_name = task_run.step_run.template.name
        attempt_id = task_run_attempt.id.hex
        name_base = '-'.join([hostname, step_name])
        sanitized_name_base = cls.sanitize_instance_name_base(name_base)
        sanitized_name_base = sanitized_name_base[:53]      # leave 10 characters at the end for location id and -disk suffix

        instance_name = '-'.join([sanitized_name_base, attempt_id])
        sanitized_instance_name = cls.sanitize_instance_name(instance_name)
        sanitized_instance_name = sanitized_instance_name[:58]      # leave 5 characters for -disk suffix
        return sanitized_instance_name

    @classmethod
    def sanitize_instance_name_base(cls, name):
        """ Instance names must start with a lowercase letter. All following characters must be a dash, lowercase letter, or digit. """
        name = str(name).lower()                # make all letters lowercase
        name = re.sub(r'[^-a-z0-9]', '', name)  # remove invalid characters
        name = re.sub(r'^[^a-z]+', '', name)    # remove non-lowercase letters from the beginning
        return name

    @classmethod
    def sanitize_instance_name(cls, name):
        """ Instance names must start with a lowercase letter. All following characters must be a dash, lowercase letter, or digit. Last character cannot be a dash.
        Instance names must be 1-63 characters long.
        """
        name = str(name).lower()                # make all letters lowercase
        name = re.sub(r'[^-a-z0-9]', '', name)  # remove invalid characters
        name = re.sub(r'^[^a-z]+', '', name)    # remove non-lowercase letters from the beginning
        name = re.sub(r'-+$', '', name)         # remove dashes from the end
        name = name[:63]                        # truncate if too long
        if len(name) < 1:               
            raise CloudTaskManagerError('Cannot create an instance name from %s' % name)
            
        sanitized_name = name
        return sanitized_name


class CloudTaskManagerError(Exception):
    pass
