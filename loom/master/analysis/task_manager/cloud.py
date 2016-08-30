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

import loom.common.logger
import loom.common.version
import loom.common.cloud

PLAYBOOKS_PATH = os.path.join(imp.find_module('loom')[1], 'playbooks')
GCLOUD_CREATE_WORKER_PLAYBOOK = os.path.join(PLAYBOOKS_PATH, 'gcloud_create_worker.yml')
GCLOUD_CREATE_WORKER_SKIP_INSTALLS_PLAYBOOK = os.path.join(PLAYBOOKS_PATH, 'gcloud_create_worker_skip_installs.yml')
GCLOUD_RUN_TASK_PLAYBOOK = os.path.join(PLAYBOOKS_PATH, 'gcloud_run_task.yml')
GCE_PY_PATH = os.path.join(imp.find_module('loom')[1], 'common', 'gce.py')
LOOM_USER_SSH_KEY_FILE = '/home/loom/.ssh/google_compute_engine'

class CloudTaskManager:

    @classmethod
    def run(cls, task_run):
        from analysis.models.task_runs import TaskRunAttempt
        task_run_attempt = TaskRunAttempt.create_from_task_run(task_run)
        logger = loom.common.logger.get_logger('TaskManagerLogger', logfile=os.path.join(settings.LOGS_DIR, 'loom_cloud_taskmanager.log'))
        
        # Don't want to block while waiting for VM to come up, so start another process to finish the rest of the steps.
        logger.debug("Launching CloudTaskManager as a separate process.")
        #task_run_attempt_pickle = pickle.dumps(task_run_attempt)
        #logger.debug("task_run_attempt: %s" % task_run_attempt)

        requested_resources = {
            'cores': task_run_attempt.task_run.step_run.resources.cores,
            'memory': task_run_attempt.task_run.step_run.resources.memory,
            'disk_size': task_run_attempt.task_run.step_run.resources.disk_size,
        }
        environment = {
            'docker_image': task_run_attempt.task_definition.environment.docker_image,
        }
        
        hostname = socket.gethostname()
        node_name = cls.create_worker_name(hostname, task_run_attempt)
        task_run_attempt_id = task_run_attempt.id.hex
        
        process = multiprocessing.Process(target=CloudTaskManager._run, args=(task_run_attempt_id, requested_resources, environment, node_name,))
        process.start()

    @classmethod
    def _run(cls,task_run_attempt_id, requested_resources, environment, node_name):
        logger = loom.common.logger.get_logger('TaskManagerLogger')
        logger.debug("CloudTaskManager separate process started.")
        logger.debug("task_run_attempt: %s" % task_run_attempt_id)
        """Create a VM, deploy Docker and Loom, and pass command to task runner."""
        if settings.WORKER_TYPE != 'GOOGLE_CLOUD':
            raise CloudTaskManagerError('Unsupported cloud type: ' + settings.WORKER_TYPE)
        # TODO: Support other cloud providers. For now, assume GCE.
        instance_type = CloudTaskManager._get_cheapest_instance_type(cores=requested_resources['cores'], memory=requested_resources['memory'])
        
        scratch_disk_name = node_name+'-disk'
        scratch_disk_device_path = '/dev/disk/by-id/google-'+scratch_disk_name
        if requested_resources.get('disk_size') is not None:
            scratch_disk_size_gb = requested_resources['disk_size']
        else:   
            scratch_disk_size_gb = settings.WORKER_SCRATCH_DISK_SIZE
        
        playbook_vars = {
            'node_name': node_name,
            'image': settings.WORKER_VM_IMAGE,
            'instance_type': instance_type,
            'scratch_disk_name': scratch_disk_name,
            'scratch_disk_device_path': scratch_disk_device_path,
            'scratch_disk_mount_point': settings.WORKER_SCRATCH_DISK_MOUNT_POINT,
            'scratch_disk_type': settings.WORKER_SCRATCH_DISK_TYPE,
            'scratch_disk_size_gb': scratch_disk_size_gb,
            'boot_disk_type': settings.WORKER_BOOT_DISK_TYPE,
            'boot_disk_size_gb': settings.WORKER_BOOT_DISK_SIZE,
            'zone': settings.WORKER_LOCATION,
            'task_run_attempt_id': task_run_attempt_id,
            'task_run_docker_image': environment['docker_image'],
            'master_url': settings.MASTER_URL_FOR_WORKER,
            'version': loom.common.version.version(),
            'worker_network': settings.WORKER_NETWORK,
            'worker_tags': settings.WORKER_TAGS,
            'docker_full_name': settings.DOCKER_FULL_NAME,
            'docker_tag': settings.DOCKER_TAG,
        }
        logger.debug('Starting worker VM using playbook vars: %s' % playbook_vars)
        ansible_logfile=open(os.path.join(settings.LOGS_DIR, 'loom_ansible.log'), 'a', 0)
        if settings.WORKER_SKIP_INSTALLS == "True":
            cls._run_playbook(GCLOUD_CREATE_WORKER_SKIP_INSTALLS_PLAYBOOK, playbook_vars, logfile=ansible_logfile)
        else:
            cls._run_playbook(GCLOUD_CREATE_WORKER_PLAYBOOK, playbook_vars, logfile=ansible_logfile)
        cls._run_playbook(GCLOUD_RUN_TASK_PLAYBOOK, playbook_vars, logfile=ansible_logfile)
        logger.debug("CloudTaskManager process done.")
        ansible_logfile.close()

    @classmethod
    def _run_playbook(cls, playbook, playbook_vars, logfile=None):
        """ Runs a playbook by passing it a dict of vars on the command line."""
        ansible_env = os.environ.copy()
        ansible_env['ANSIBLE_HOST_KEY_CHECKING'] = 'False'
        ansible_env['INVENTORY_IP_TYPE'] = 'internal'       # Tell gce.py to use internal IP for ansible_ssh_host
        os.chmod(GCE_PY_PATH, 0755)                         # Make sure dynamic inventory is executable
        playbook_vars_json_string = json.dumps(playbook_vars)
        subprocess.call(['ansible-playbook', '-vvv', '--key-file', LOOM_USER_SSH_KEY_FILE, '-i', GCE_PY_PATH, playbook, '--extra-vars', playbook_vars_json_string], env=ansible_env, stderr=subprocess.STDOUT, stdout=logfile)

    @classmethod
    def _get_cheapest_instance_type(cls, cores, memory):
        """ Determine the cheapest instance type given a minimum number of cores and minimum amount of RAM (in GB). """

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
        """ Retrieve latest pricelist from Google Cloud, or use cached copy if not reachable. """
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
    def delete_node_by_name(cls, node_name):
        """ Delete the node that ran a task. """
        # Don't want to block while waiting for VM to be deleted, so start another process to finish the rest of the steps.
        process = multiprocessing.Process(target=CloudTaskManager._delete_node, args=(node_name))
        process.start()

    @classmethod
    def delete_node_by_task_run(cls, host_name, task_run):
        """ Delete the node that ran a task. """
        node_name = cls.create_worker_name(host_name, task_run)
        cls.delete_node_by_name(node_name)
        
    @classmethod
    def _delete_node(cls, node_name):
        if settings.WORKER_TYPE != 'GOOGLE_CLOUD':
            raise CloudTaskManagerError('Unsupported cloud type: ' + settings.WORKER_TYPE)
        # TODO: Support other cloud providers. For now, assume GCE.
        zone = settings.WORKER_LOCATION
        s = Template(
"""---
- hosts: localhost
  connection: local
  tasks:
  - name: Delete a node.
    gce: name=$node_name zone=$zone state=deleted
""")
        playbook = s.substitute(locals())
        cls._run_playbook_string(playbook)
        # TODO: Delete scratch disk

    @classmethod
    def create_worker_name(cls, hostname, task_run_attempt):
        """ Create a name for the worker instance. Since hostname, workflow name, and step name can easily be duplicated,
        we do this in two steps to ensure that at least 4 characters of the location ID are part of the name.
        Also, worker scratch disks are named by appending '-disk' to the instance name, and disk names are max 63 characters,
        so leave 5 characters for the '-disk' suffix.
        """
        task_run = task_run_attempt.task_run
        #workflow_name = task_run.workflow_name
        step_name = task_run.step_run.template.name
        attempt_id = task_run_attempt.id.hex
        name_base = '-'.join([hostname, step_name])
        sanitized_name_base = cls.sanitize_instance_name_base(name_base)
        sanitized_name_base = sanitized_name_base[:53]      # leave 10 characters at the end for location id and -disk suffix

        node_name = '-'.join([sanitized_name_base, attempt_id])
        sanitized_node_name = cls.sanitize_instance_name(node_name)
        sanitized_node_name = sanitized_node_name[:58]      # leave 5 characters for -disk suffix
        return sanitized_node_name

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
