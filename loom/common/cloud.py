import gcloud.storage
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

def create_bucket(bucket_name):
    """ Create a storage bucket using project and credentials inferred from the environment."""
    client = gcloud.storage.Client()
    bucket = client.create_bucket(bucket_name)
    return bucket
