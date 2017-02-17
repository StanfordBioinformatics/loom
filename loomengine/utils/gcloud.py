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

def get_worker_name(hostname, step_name, attempt_id):
    """Create a name for the worker instance that will run the specified task run attempt, from this server.
    Since hostname, workflow name, and step name can easily be duplicated,
    we do this in two steps to ensure that at least 4 characters of the
    location ID are part of the name. Also, since worker scratch disks are
    named by appending '-disk' to the instance name, and disk names are max
    63 characters, leave 5 characters for the '-disk' suffix.
    """
    name_base = '-'.join([hostname, step_name])
    sanitized_name_base = sanitize_instance_name_base(name_base)
    sanitized_name_base = sanitized_name_base[:53]      # leave 10 characters at the end for location id and -disk suffix

    instance_name = '-'.join([sanitized_name_base, attempt_id])
    sanitized_instance_name = sanitize_instance_name(instance_name)
    sanitized_instance_name = sanitized_instance_name[:58]      # leave 5 characters for -disk suffix
    print sanitized_instance_name
    return sanitized_instance_name

def sanitize_instance_name_base(name):
    """ Instance names must start with a lowercase letter. All following characters must be a dash, lowercase letter, or digit. """
    name = str(name).lower()                # make all letters lowercase
    name = re.sub(r'[^-a-z0-9]', '', name)  # remove invalid characters
    name = re.sub(r'^[^a-z]+', '', name)    # remove non-lowercase letters from the beginning
    return name

def sanitize_instance_name(name):
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
