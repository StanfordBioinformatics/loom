#!/usr/bin/env python3

"""Pipeline runner. Stays running, wakes up every specified time interval, gets analyses from the server, downloads input files,
runs analyses, uploads output files, and updates the server with analysis status.

If DAEMON = True, runs as a detached process, writing stdout and stderr to log files in the current directory.

State transition diagram for analyses: ready --> (downloading) --> running --> (uploading) --> done
"""

import os
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
_STORAGE_ACCOUNT_KEY = '' # moved to external JSON
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
    return json_response

def update_analysis(analysis):
    """Check the status of an analysis, including its running subprocesses, launch the next step if applicable, and update analysis status."""
    if analysis['status'] == 'ready':
        start_downloading(analysis)
    if analysis['status'] == 'downloading':
        if current_step_complete(analysis):
            if all_steps_complete(analysis):
                start_running(analysis)
            else:
                start_next_step(analysis)
    if analysis['status'] == 'running':
        if current_step_complete(analysis):
            if all_steps_complete(analysis):
                start_uploading(analysis)
            else:
                start_next_step(analysis)
    if analysis['status'] == 'uploading':
        if current_step_complete(analysis):
            if all_steps_complete(analysis):
                analysis['status'] = 'done'
            else:
                start_next_step(analysis)
    
def current_step_complete(analysis):
    status = check_process(analysis['current_process'])
    if status == 'done':
        return True
    elif status == 'running':
        return False
    else:
        raise Exception('Process failed with return code ' + status)

def all_steps_complete(analysis):
    if analysis['status'] == 'downloading':
        num_steps = len(analysis['files']['imports'])
    elif analysis['status'] == 'running':
        num_steps = len(analysis['steps'])
    elif analysis['status'] == 'uploading':
        num_steps = len(analysis['files']['exports'])
    else:
        raise Exception('Unrecognized analysis status for step completion check: ' + analysis['status'])
        
    if current_step_complete(analysis) and analysis['step_counter'] + 1 >= num_steps:
        return True
    else:
        return False

def start_downloading(analysis):
    imports = analysis['files']['imports']
    if len(imports) < 1:
        start_running(analysis)
    else:
        download_step(analysis, 0)
        analysis['status'] = 'downloading'
        
def download_step(analysis, n):
        importfile = analysis['files']['imports'][n]
        analysis['step_counter'] = n
        analysis['current_process'] = download_file(importfile['account'], _STORAGE_ACCOUNT_KEY, importfile['container'], importfile['blob'], importfile['local_path']) 

def start_uploading(analysis):
    exports = analysis['files']['exports']
    if len(exports) < 1:
        analysis['status'] = 'done'
    else:
        upload_step(analysis, 0)
        analysis['status'] = 'uploading'

def upload_step(analysis, n):
        exportfile = analysis['files']['exports'][n]
        analysis['step_counter'] = n
        analysis['current_process'] = upload_file(exportfile['account'], _STORAGE_ACCOUNT_KEY, exportfile['container'], exportfile['blob'], exportfile['local_path']) 

def start_running(analysis):
    if len(analysis['steps']) < 1:
        start_uploading(analysis)
    else:
        run_step(analysis, 0)
        analysis['status'] = 'running'

def run_step(analysis, n):
        step = analysis['steps'][n]
        docker_image = step['docker_image']
        command = step['command']
        analysis['step_counter'] = n
        analysis['current_process'] = run_command(docker_image, command)

def start_next_step(analysis):
    n = analysis['step_counter'] + 1
    if analysis['status'] == 'downloading':
        download_step(analysis, n)
    elif analysis['status'] == 'running':
        run_step(analysis, n)
    elif analysis['status'] == 'uploading':
        upload_step(analysis, n)
    else:
        raise Exception('Unrecognized analysis status for starting next step: ' + analysis['status'])

def run_command(image, command):
    """Run command using Docker image."""
    cmd = 'sudo docker run ' + image + ' ' + command    
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

def update_server(analysis_id, status):
    """Update the server with the current status of an analysis."""
    data_pkg = json.dumps({'status':status})
    r=requests.update(_ANALYSES_URL + '/' + str(analysis_id), data=data_pkg, headers = _HEADERS)

def download_file(account, key, remotecontainer, remoteblob, localfile):
    return transfer_file(account, key, localfile, remotecontainer, remoteblob, '--forcedownload')

def upload_file(account, key, localfile, remotecontainer, remoteblob):
    return transfer_file(account, key, localfile, remotecontainer, remoteblob, '--forceupload')

def transfer_file(account, key, localfile, remotecontainer, remoteblob, direction):
    # Requires blobxfer.py; seems to have a bug with transferring empty files
    return subprocess.Popen(['./blobxfer.py', direction, '--remoteresource', remoteblob, '--storageaccountkey', key, account, remotecontainer, localfile]) 

def main():
    """Runs as a detached process, writing stdout and stderr to log files in the current directory."""
    if _DAEMON:
        daemon_context = daemon.DaemonContext(
            working_directory='.',
            stdout=open('out.log', 'w'),
            stderr=open('err.log', 'w')
            )
        daemon_context.open()

    # Open config JSON file and read inputs.
    xppfroot = os.environ['XPPFROOT']
    with open(os.path.join(xppfroot, 'duckling', 'duckling.json')) as configfile:
        config = json.load(configfile)
        _STORAGE_ACCOUNT_KEY = config['_STORAGE_ACCOUNT_KEY']
        
    analyses = {}
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
            update_analysis(analysis)

            # Update server with status of analysis
            if analysis['status'] == 'downloading' or analysis['status'] == 'running' or analysis['status'] == 'uploading':
                update_server(analysis_id, 1) #1 = running
                print('Updating server, analysis:', analysis_id, 'status: running')
            elif analysis['status'] == 'done':
                update_server(analysis_id, 2) #2 = done
                print('Updating server, analysis:', analysis_id, 'status: done')

        # Go back to sleep
        time.sleep(_SLEEP_INTERVAL) 

if __name__ == "__main__":
    main()

