import errno 
import json
import logging
import multiprocessing
import os
import requests
import subprocess
import tempfile
from string import Template

import oauth2client.contrib.gce
from django.conf import settings

logger = logging.getLogger('LoomDaemon')


class CloudTaskManager:

    inventory_file = ''

    @classmethod
    def run(cls, task_run):
        # Don't want to block while waiting for VM to come up, so start another process to finish the rest of the steps.
        process = multiprocessing.Process(target=CloudTaskManager._run, args=(task_run))
        process.start()

    @classmethod
    def _run(cls, task_run):
        """Create a VM, deploy Docker and Loom, and pass command to task runner."""
        if settings.MASTER_TYPE != 'GOOGLE_CLOUD':
            raise CloudTaskManagerError('Unsupported cloud type: ' + settings.MASTER_TYPE)
        # TODO: Support other cloud providers. For now, assume GCE.
        cls._setup_ansible_gce()
        resources = CloudTaskManager._get_resource_requirements(task_run)
        instance_type = CloudTaskManager._get_cheapest_instance_type(cores=resources.cores, memory=resources.memory)
        task_id = task_run.id # TODO: point to actual TaskRun id after merging
        node_name = task_id
        disk_name = node_name+'-disk'
        device_path = '/dev/disk/by-id/google-'+disk_name
        playbook = cls._create_taskrun_playbook(node_name, settings.WORKER_VM_IMAGE, instance_type, disk_name, device_path, mount_point=settings.WORKER_DISK_MOUNT_POINT, disk_type=settings.WORKER_DISK_TYPE, size_gb=settings.WORKER_DISK_SIZE, zone=settings.WORKER_LOCATION)
        cls._run_playbook_string(playbook)

    @classmethod
    def _create_taskrun_playbook(cls, node_name, image, instance_type, disk_name, device_path, mount_point, disk_type, size_gb, zone):
        s = Template(
"""---
- name: Create new instance.
  hosts: localhost
  connection: local
  gather_facts: no
  tasks:
  - name: Boot up a new instance.
    gce: name=$node_name zone=$zone image=$image machine_type=$instance_type 
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
  - name: Install pip and virtualenv using apt-get.
    apt: update_cache=yes
""")
# TODO: install pip, deploy Loom, and run a command
        return s.substitute(locals())

    @classmethod
    def _run_playbook_string(cls, playbook_string):
        """ Runs a string as a playbook by writing it to a tempfile and passing the filename to ansible-playbook. """
        ansible_env = os.environ.copy()
        ansible_env['ANSIBLE_HOST_KEY_CHECKING'] = 'False'
        with tempfile.NamedTemporaryFile() as playbook:
            playbook.write(playbook_string)
            playbook.flush()
            subprocess.call(['ansible-playbook', '-vvvv', '--key-file', settings.GCE_KEY_FILE, '-i', cls.inventory_file, playbook.name], env=ansible_env)

    @classmethod
    def _setup_ansible_gce(cls):
        """ Make sure dynamic inventory from ansible.contrib is executable, and write credentials to secrets.py. """
        cls.inventory_file = os.path.join(os.path.dirname(__file__), 'ansible.contrib.inventory.gce.py')
        os.chmod(cls.inventory_file, 0755)
        gce_credentials = oauth2client.contrib.gce.AppAssertionCredentials([])
        credentials = { 'service_account_email': gce_credentials.service_account_email,
                        'pem_file': settings.ANSIBLE_PEM_FILE,
                        'project_id': settings.PROJECT_ID }
        # Write a secrets.py somewhere on the Python path for Ansible to import.
        # Assumes loom is on the Python path.
        import loom
        loomparentdir = os.path.dirname(os.path.dirname(loom.__file__))
        with open(os.path.join(loomparentdir, 'secrets.py'), 'w') as outfile:
            outfile.write("GCE_PARAMS=('"+credentials['service_account_email']+"', '"+credentials['pem_file']+"')\n")
            outfile.write("GCE_KEYWORD_PARAMS={'project': '"+credentials['project_id']+"'}")
        try:
            import secrets
        except ImportError:
            raise CloudTaskManagerError("Couldn't write secrets.py to the Python path")
    
    @classmethod
    def _get_resource_requirements_django(cls, task_run):
        # TODO: use this again when we have a TaskRun Django model
        # Retrieve resource requirements
        # If step_run has more than one step, requirements
        # should be identical in all steps.
        resources = None
        last_resources = None
        for task in task_run.tasks.all():
            resources = task.resources
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
    def _get_resource_requirements(cls, task_run):
        """ Just return the resources for the first task for now."""
        return task_run.tasks[0]

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
    def delete_node(cls, task_run):
        """ Delete the node that ran a task. """
        # Don't want to block while waiting for VM to come up, so start another process to finish the rest of the steps.
        process = multiprocessing.Process(target=CloudTaskManager._delete_node, args=(task_run))
        process.start()
        
    @classmethod
    def _delete_node(cls, task_run):
        node_name=task_run.id
        s = Template(
"""---
- hosts: localhost
  connection: local
  tasks:
  - name: Delete a node.
    gce: name=$node_name zone=$zone state=deleted
""")
# TODO: install pip, deploy Loom, and run a command
        return s.substitute(locals())
        




    @classmethod
    def old_deploy(cls):
    	CloudTaskManager._create_file_root_on_worker()

        # Construct command to run on worker node
        cmd = '%s %s --run_id %s --master_url %s' % (
            PYTHON_EXECUTABLE,
            STEP_RUNNER_EXECUTABLE,
            step_run.id,
            settings.MASTER_URL_FOR_WORKER,
            )
        if step_run.steps.count() == 0:
            raise Exception("No Step found for StepRun %s" % step_run.id)

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
