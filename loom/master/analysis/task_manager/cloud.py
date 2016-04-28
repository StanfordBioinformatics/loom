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

import oauth2client.contrib.gce
from django.conf import settings

import loom.common.logger
import loom.common.version

class CloudTaskManager:

    inventory_file = ''

    @classmethod
    def run(cls, task_run, task_run_location_id, requested_resources):
        logger = loom.common.logger.get_logger('TaskManagerLogger', logfile='/tmp/loom_cloud_taskmanager.log')
        
        # Don't want to block while waiting for VM to come up, so start another process to finish the rest of the steps.
        logger.debug("Launching CloudTaskManager as a separate process.")
        task_run_pickle = pickle.dumps(task_run)
        logger.debug("task_run_pickle: %s, task_run_location_id: %s, requested_resources: %s" % (task_run_pickle, task_run_location_id, requested_resources))
        process = multiprocessing.Process(target=CloudTaskManager._run, args=(task_run_pickle, task_run_location_id, requested_resources))
        process.start()

    @classmethod
    def _run(cls, task_run_pickle, task_run_location_id, requested_resources):
        task_run = pickle.loads(task_run_pickle)
        logger = loom.common.logger.get_logger('TaskManagerLogger')
        logger.debug("CloudTaskManager separate process started.")
        logger.debug("task_run: %s, task_run_location_id: %s, requested_resources: %s" % (task_run, task_run_location_id, requested_resources))
        """Create a VM, deploy Docker and Loom, and pass command to task runner."""
        if settings.WORKER_TYPE != 'GOOGLE_CLOUD':
            raise CloudTaskManagerError('Unsupported cloud type: ' + settings.WORKER_TYPE)
        # TODO: Support other cloud providers. For now, assume GCE.
        cls._setup_ansible_gce()
        instance_type = CloudTaskManager._get_cheapest_instance_type(cores=requested_resources.cores, memory=requested_resources.memory)
        hostname = socket.gethostname()
        node_name_to_sanitize = '%s-worker-%s-%s-%s' % (hostname, task_run.workflow_name, task_run.step_name, task_run_location_id) # GCE instance names must start with a lowercase letter; just using ID's can start with numbers.
        node_name = cls.sanitize_instance_name(node_name_to_sanitize)
        disk_name = node_name+'-disk'
        device_path = '/dev/disk/by-id/google-'+disk_name
        if hasattr(requested_resources, 'disk_size'):
            disk_size_gb = requested_resources.disk_size
        else:   
            disk_size_gb = settings.WORKER_DISK_SIZE
        
        if len(settings.WORKER_TAGS.strip()) == 0:
            worker_tags = ''
        else:
            worker_tags = 'tags=%s' % settings.WORKER_TAGS
        
        playbook_values = {
            'node_name': node_name,
            'image': settings.WORKER_VM_IMAGE,
            'instance_type': instance_type,
            'disk_name': disk_name,
            'device_path': device_path,
            'mount_point': settings.WORKER_DISK_MOUNT_POINT,
            'disk_type': settings.WORKER_DISK_TYPE,
            'size_gb': disk_size_gb,
            'zone': settings.WORKER_LOCATION,
            'run_id': task_run._id,
            'run_location_id': task_run_location_id,
            'master_url': settings.MASTER_URL_FOR_WORKER,
            'version': loom.common.version.version(),
            'worker_network': settings.WORKER_NETWORK,
            'worker_tags': worker_tags,
        }
        playbook = cls._create_taskrun_playbook(playbook_values)
        logger.debug('Starting worker VM using playbook: %s' % playbook)
        ansible_logfile=open('/tmp/loom_ansible.log', 'a', 0)
        cls._run_playbook_string(playbook, ansible_logfile)
        logger.debug("CloudTaskManager process done.")
        ansible_logfile.close()

    @classmethod
    def _create_taskrun_playbook(cls, playbook_values_dict):
        s = Template(
"""---
- name: Create new instance.
  hosts: localhost
  connection: local
  gather_facts: no
  tasks:
  - name: Boot up a new instance.
    gce: name=$node_name zone=$zone image=$image machine_type=$instance_type network=$worker_network service_account_permissions=storage-rw $worker_tags
    register: gce_result
  - name: Create a disk and attach it to the instance.
    gce_pd: instance_name=$node_name name=$disk_name disk_type=$disk_type size_gb=$size_gb zone=$zone mode=READ_WRITE
  - name: Wait for SSH to come up.
    wait_for: host={{ item.private_ip }} port=22 delay=10 timeout=60
    with_items: '{{ gce_result.instance_data }}'
  - name: Add host to groupname.
    add_host: hostname={{ item.private_ip }} groupname=new_instances
    with_items: '{{ gce_result.instance_data }}'
- name: Set up new instance(s).
  hosts: new_instances
  become: yes
  become_method: sudo
  tasks:
  - name: Create a filesystem on the disk.
    filesystem: fstype=ext4 dev=$device_path force=no
  - name: Create the mount point.
    file: path=$mount_point state=directory
  - name: Mount the disk at the mount point.
    mount: name=$mount_point fstype=ext4 src=$device_path state=mounted
  - name: Update apt-get's cache.
    apt: update_cache=yes
  - name: Install pip using apt-get.
    apt: name=python-pip state=present
  - name: Install python-dev using apt-get, which is needed to build certain Python dependencies.
    apt: name=python-dev state=present
  - name: Install build-essential using apt-get, which is needed to build certain Python dependencies.
    apt: name=build-essential state=present
  - name: Install libffi-dev using apt-get, which is needed to build certain Python dependencies.
    apt: name=libffi-dev state=present
  - name: Install virtualenv using pip.
    pip: name=virtualenv state=present
  - name: Install Loom using pip in a virtualenv. Make sure to install the same version on the worker as the master.
    pip: name=loomengine virtualenv=/opt/loom version=$version
  - name: Run the Loom task runner.
    shell: source /opt/loom/bin/activate; loom-taskrunner --run_id $run_id --run_location_id $run_location_id --master_url $master_url
    args:
      executable: /bin/bash
""")
        return s.substitute(playbook_values_dict)

    @classmethod
    def _run_playbook_string(cls, playbook_string, logfile=None):
        """ Runs a string as a playbook by writing it to a tempfile and passing the filename to ansible-playbook. """
        ansible_env = os.environ.copy()
        ansible_env['ANSIBLE_HOST_KEY_CHECKING'] = 'False'
        with tempfile.NamedTemporaryFile() as playbook:
            playbook.write(playbook_string)
            playbook.flush()
            subprocess.call(['ansible-playbook', '--key-file', settings.GCE_KEY_FILE, '-i', cls.inventory_file, playbook.name], env=ansible_env, stderr=subprocess.STDOUT, stdout=logfile)

    @classmethod
    def _setup_ansible_gce(cls):
        """ Make sure dynamic inventory from ansible.contrib is executable, and write credentials to secrets.py. """
        # Assumes loom is on the Python path.
        loom_location = imp.find_module('loom')[1]
        loomparentdir = os.path.dirname(loom_location)
        cls.inventory_file = os.path.join(loomparentdir, 'loom', 'master', 'analysis', 'task_manager', 'ansible.contrib.inventory.gce.py')
        os.chmod(cls.inventory_file, 0755)
        gce_credentials = oauth2client.contrib.gce.AppAssertionCredentials([])
        credentials = { 'service_account_email': gce_credentials.service_account_email,
                        'pem_file': settings.ANSIBLE_PEM_FILE,
                        'project_id': settings.PROJECT_ID }

        # Write a secrets.py somewhere on the Python path for Ansible to import.
        loom_location = imp.find_module('loom')[1]
        loomparentdir = os.path.dirname(loom_location)
        with open(os.path.join(loomparentdir, 'secrets.py'), 'w') as outfile:
            outfile.write("GCE_PARAMS=('"+credentials['service_account_email']+"', '"+credentials['pem_file']+"')\n")
            outfile.write("GCE_KEYWORD_PARAMS={'project': '"+credentials['project_id']+"'}")
        try:
            import secrets
        except ImportError:
            raise CloudTaskManagerError("Couldn't write secrets.py to the Python path")

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
    def delete_node_by_task_run(cls, task_run):
        """ Delete the node that ran a task. """
        # Don't want to block while waiting for VM to be deleted, so start another process to finish the rest of the steps.
        process = multiprocessing.Process(target=CloudTaskManager._delete_node, args=(task_run._id))
        process.start()
        
    @classmethod
    def _delete_node(cls, node_name):
        if settings.WORKER_TYPE != 'GOOGLE_CLOUD':
            raise CloudTaskManagerError('Unsupported cloud type: ' + settings.WORKER_TYPE)
        # TODO: Support other cloud providers. For now, assume GCE.
        cls._setup_ansible_gce()
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

    @classmethod
    def sanitize_instance_name(cls, name):
        """ Instance names must start with a lowercase letter. All following characters must be a dash, lowercase letter, or digit. Last character cannot be a dash.
        Instance names must be 1-63 characters long.
        """
        name = str(name).lower()                # make all letters lowercase
        name = re.sub(r'[^-a-z0-9]', '', name)  # remove invalid characters
        name = re.sub(r'^[^a-z]+', '', name)    # remove non-lowercase letters from the beginning
        name = re.sub(r'-+$', '', name)         # remove dashes from the end
        if len(name) > 58:                      # truncate if too long; limit to 58 characters to leave room for '-disk' suffix
            name = name[:58]
        if len(name) < 1:               
            name = 'loom-instance'              # default name if too short 
            
        sanitized_name = name
        return sanitized_name


class CloudTaskManagerError(Exception):
    pass
