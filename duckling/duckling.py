#!/usr/bin/env python3

"""Pipeline runner. Stays running, wakes up every specified time interval, gets analyses from the server, downloads input files,
runs analyses, uploads output files, and updates the server with analysis status.

If DAEMON = True, runs as a detached process, writing stdout and stderr to log files in the current directory.

State transition diagram for analyses: ready --> (downloading) --> running --> (uploading) --> done
"""

import subprocess
import time
import json
import logging
import requests
import daemon
from pprint import pprint

_DAEMON = False
_SLEEP_INTERVAL = 5
_SERVER_URL = 'http://localhost:80'
_ANALYSES_URL = _SERVER_URL + '/analyses'
_STATUS_URL = _SERVER_URL + '/status'
_STORAGE_ACCOUNT_KEY = '8hz9b5H3broyRlJTxMDFPR2b+LeYrpbD18PZZrbOZ8SNV35IGwL2IXvAgCzJ7qMd4s0LQDqcPS6t+OR4rW6OcQ=='
_STORAGE_ACCOUNT_NAME = 'scgs'
_HEADERS = {'Content-type':'application/json','Accept':'text/plain'}

def check_server_status():
    r=requests.get(_STATUS_URL)
    return r

def get_ready_analyses():
    """Get list of ready analyses."""
    r=requests.get(_ANALYSES_URL, params={'status':'ready'}) 
    json_response = json.loads(r.json())
    return json_response

def get_analysis(analysis_id):
    """Retrieve contents of the specified analysis."""
    data_pkg = json.dumps({'analysis_id':analysis_id})
    r=requests.get(_ANALYSES_URL, data=data_pkg, headers = _HEADERS)
    json_response = json.loads(r.json())
    return json_response[0]
    
def run_analysis(container, command):
    """Run the analysis."""
    cmd = 'sudo docker run ' + container + ' ' + command    
    return subprocess.Popen(cmd, shell=True)

def check_process(process):
    """Check the status of the given process and return it."""
    returncode = process.returncode
    if returncode is None:
        return 'running'
    elif returncode == 0:
        return 'done'
    else:
        return str(returncode)

def update_analysis(analysis_id, status):
    """Update the server with the current status of an analysis."""
    data_pkg = json.dumps({'status':status})
    r=requests.update(_ANALYSES_URL + '/' + str(analysis_id), data=data_pkg, headers = _HEADERS)

def download_file(remotecontainer, remoteblob, localfile):
    transfer_file(localfile, remotecontainer, remoteblob)

def upload_file(localfile, remotecontainer, remoteblob):
    transfer_file(localfile, remotecontainer, remoteblob)

def transfer_file(localfile, remotecontainer, remoteblob):
    # Requires blobxfer.py; seems to have a bug with transferring empty files
    subprocess.call(['./blobxfer.py', '--remoteresource', remoteblob, '--storageaccountkey', _STORAGE_ACCOUNT_KEY, _STORAGE_ACCOUNT_NAME, remotecontainer, localfile]) 

def main():
    """Runs as a detached process, writing stdout and stderr to log files in the current directory."""
    if _DAEMON:
        daemon_context = daemon.DaemonContext(
            working_directory='.',
            stdout=open('out.log', 'w'),
            stderr=open('err.log', 'w')
            )
        daemon_context.open()

    running_analyses = []
    analyses = {}
    processes = {}
    while(True):
        # Check server status
        current_status = check_server_status()
        print('Current server status:', current_status)

        # Check for ready analyses
        ready_analyses = get_ready_analyses()        
        print(len(ready_analyses), 'analyses ready')
        #pprint(ready_analyses)

        # Grab details for ready analyses and add them to the analyses dict
        for analysis in ready_analyses:
            analysis_id = analysis['fields']['analysis']
            analysis_details = get_analysis(analysis_id)
            print('Analysis id', analysis_id)
            pprint(analysis_details)
            if analysis_id not in analyses:
                analyses[analysis_id] = analysis_details
                analyses[analysis_id]['status'] = 'ready'

        # Check each analysis in the dict and update as necessary
        for analysis_id in analyses:
            analysis = analyses[analysis_id]
            status = analysis['status']
            if status == 'ready':
            elif status == 'downloading':
            elif status == 'running':
            elif status == 'uploading':
            elif status == 'done':

        # Run ready analyses
        #importfiles = analysis['files']['imports']
        #exportfiles = analysis['files']['exports']
        for step in ready_analyses['steps']:
            container = step['container']
            command = step['command']
            process = run_analysis(container, command)
            print('Running command \"',command,'\" in container',container)

            analysis_id = analysis['analysisid']
            running_analyses.append(analysis_id)
            processes[analysis_id] = process

        # Update server with status of each analysis
        completed_analyses = []
        for analysis_id in running_analyses:
            process = processes[analysis_id]
            status = check_process(process)
            update_analysis(analysis_id, status)
            print('Updating server, analysis:', analysis_id, 'status:', status)

            if status == 'done':
                completed_analyses.append(analysis_id)
        
        # Remove completed analyses from the list of running analyses
        for analysis_id in completed_analyses:
            running_analyses.remove(analysis_id)

        # Go back to sleep
        time.sleep(_SLEEP_INTERVAL) 

if __name__ == "__main__":
    main()

