import json
import os
import re
import requests

# Utility functions related to Google Cloud Platform that can be used by all components.

def on_gcloud_vm():
    """ Determines if we're running on a GCE instance."""
    r = None
    try:
        r = requests.get('http://metadata.google.internal')
    except requests.ConnectionError:
        return False

    try:
        if r.headers['Metadata-Flavor'] == 'Google' and r.headers['Server'] == 'Metadata Server for VM':
            return True
    except KeyError:
        return False

def get_cheapest_instance_type(cores, memory):
    """Determine the cheapest instance type given a minimum number of cores and minimum amount of RAM (in GB)."""

    pricelist = get_gcloud_pricelist()

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
            print instance_type['name']
            return instance_type['name']

    # No instance type found that can fulfill requested cores and memory
    raise Exception('No instance type found with at least %d cores and %f GB of RAM.' % (cores, memory))

def get_gcloud_pricelist():
    """Retrieve latest pricelist from Google Cloud, or use cached copy if not reachable."""
    try:
        r = requests.get('http://cloudpricingcalculator.appspot.com/static/data/pricelist.json')
        content = json.loads(r.content)
    except ConnectionError:
        logger.warning("Couldn't get updated pricelist from http://cloudpricingcalculator.appspot.com/static/data/pricelist.json. Falling back to cached copy, but prices may be out of date.")
        with open('gcloudpricelist.json') as infile:
            content = json.load(infile)

    #logger.debug('Using pricelist ' + content['version'] + ', updated ' + content['updated'])
    pricelist = content['gcp_price_list']
    return pricelist

MIN_TASKID_CHARS = 8
def get_worker_name_base(hostname, step_name, attempt_id):
    """Create a base name for the worker instance that will run the specified task
    run attempt, from this server. Since hostname and step name will be
    duplicated across workers (reruns, etc.), ensure that at least
    MIN_TASKID_CHARS are preserved in the instance name. Also, save 5 characters
    at the end for '-disk' and '-work' suffixes, which also prevent names from ending with dashes.
    """
    name_base = '-'.join([hostname, step_name])
    sanitized_name_base = sanitize_instance_name_base(name_base)
    sanitized_name_base = sanitized_name_base[:63-5-MIN_TASK_ID_CHARS]  # leave characters at the end for task attempt id and suffixes
    worker_name_base = '-'.join([sanitized_name_base, attempt_id])
    sanitized_worker_name_base = sanitize_instance_name_base(worker_name_base)[:58] # leave 5 characters for suffixes
    return sanitized_worker_name_base

def get_worker_name(hostname, step_name, attempt_id):
    worker_name = '-'.join(get_worker_name_base(hostname, step_name, attempt_id), 'work')
    print worker_name
    return worker_name

def get_scratch_disk_name(hostname, step_name, attempt_id):
    """Create a name for the worker scratch disk."""
    disk_name = '-'.join(get_worker_name_base(hostname, step_name, attempt_id), 'disk')
    print disk_name
    return disk_name

def get_scratch_disk_device_path(hostname, step_name, attempt_id):
    """Get the device path for the worker scratch disk."""
    disk_name = get_scratch_disk_name(hostname, step_name, attempt_id)
    device_path = '-'.join('/dev/disk/by-id/google', disk_name)
    print device_path
    return device_path

def sanitize_instance_name_base(name):
    """Instance names must start with a lowercase letter. All following characters must be a dash, lowercase letter, or digit."""
    name = str(name).lower()                # make all letters lowercase
    name = re.sub(r'[^-a-z0-9]', '', name)  # remove invalid characters
    name = re.sub(r'^[^a-z]+', '', name)    # remove non-lowercase letters from the beginning
    return name
