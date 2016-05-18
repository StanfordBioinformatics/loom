import imp
import oauth2client.contrib.gce
import os
import requests
from django.conf import settings

# Common functions related to cloud platforms that can be used by all components.

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

def setup_ansible_inventory_gce():
    """ Make sure dynamic inventory from ansible.contrib is executable, and return a path to it. """
    loom_location = imp.find_module('loom')[1]
    loomparentdir = os.path.dirname(loom_location)
    inventory_file = os.path.join(loomparentdir, 'loom', 'common', 'ansible.contrib.inventory.gce.py')
    os.chmod(inventory_file, 0755)
    return inventory_file

def setup_gce_credentials():
    """ Write a secrets.py on the Python path for Ansible to import."""
    if on_gcloud_vm():
        gce_credentials = oauth2client.contrib.gce.AppAssertionCredentials([])
    else:
        raise Exception("Not running on a GCE instance, will have to get credentials another way.")
    credentials = { 'service_account_email': gce_credentials.service_account_email,
                    'pem_file': settings.ANSIBLE_PEM_FILE,
                    'project_id': settings.PROJECT_ID }
    loom_location = imp.find_module('loom')[1]
    loomparentdir = os.path.dirname(loom_location)
    with open(os.path.join(loomparentdir, 'secrets.py'), 'w') as outfile:
        outfile.write("GCE_PARAMS=('"+credentials['service_account_email']+"', '"+credentials['pem_file']+"')\n")
        outfile.write("GCE_KEYWORD_PARAMS={'project': '"+credentials['project_id']+"'}")
    try:
        import secrets
    except ImportError:
        raise Exception("Couldn't write secrets.py to the Python path.")
