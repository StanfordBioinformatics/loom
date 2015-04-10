#!/usr/bin/env python

"""Pipeline runner. Stays running, wakes up every specified time interval, gets analyses from the server, downloads input files,
runs analyses, uploads output files, and updates the server with analysis status.

If DAEMON = True, runs as a detached process, writing stdout and stderr to log files in the current directory.
"""

import subprocess
import time
import json
import logging
import requests
import daemon

_DAEMON = False
_SLEEP_INTERVAL = 5
_SERVER_URL = 'http://localhost:8000'
_ANALYSES_URL = _SERVER_URL + '/analyses'
_STATUS_URL = _SERVER_URL + '/status'
_STORAGE_ACCOUNT_KEY = '8hz9b5H3broyRlJTxMDFPR2b+LeYrpbD18PZZrbOZ8SNV35IGwL2IXvAgCzJ7qMd4s0LQDqcPS6t+OR4rW6OcQ=='
_STORAGE_ACCOUNT_NAME = 'scgs'
_HEADERS = {'Content-type':'application/json','Accept':'text/plain'}

def check_server_status():
    r=requests.get(_STATUS_URL)
    return r

def get_ready_analyses():
    """Get all ready analyses."""
    r=requests.get(_ANALYSES_URL, params={'status':'ready'}) 
    json_response = r.json()
    return json_response

def run_analysis(analysis):
    """Run the analysis."""

def update_status(analysis_id, status):
    """Update the server with the current status of an analysis."""
    data_pkg = json.dumps({'status':status})
    r=requests.update(_ANALYSES_URL + '/' + str(analysis_id), data=data_pkg, headers = _HEADERS)

def download_file(remotecontainer, remoteblob, localfile):
    transfer_file(localfile, remotecontainer, remoteblob)

def upload_file(localfile, remotecontainer, remoteblob):
    transfer_file(localfile, remotecontainer, remoteblob)

def transfer_file(localfile, remotecontainer, remoteblob):
    # Note: blobxfer.py seems to have a bug with transferring empty files
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

    while(True):
        # Check server status
        current_status = check_server_status()
        print(current_status)

        # Check for ready analyses
        analyses = get_ready_analyses()        
        print(analyses)
        print(len(analyses), 'analyses ready')

        # Run ready analyses
#         for analysis in analyses:
#             analyses = get_analysis(analysis_entry['fields']['analysis'])
#             print("\n***analyze:"+str(analyses))
#             step_i=0
#             for analysis in analyses:
#                 step_i = step_i+1
#                 container = analysis['container']
#                 command = analysis['command']
#                 print(">>>STEP "+str(step_i))
#                 print("container:"+container)
#                 print("command:"+command)

        # Update server with status of each analysis

        # Go back to sleep
        time.sleep(_SLEEP_INTERVAL) 

#    while(True):
#        print('Sleeping for', SLEEP_TIME, 'seconds')
#        time.sleep(SLEEP_TIME)   
#        print('Checking server status')
#        check_server_status(STATUS_URL)    
#        print('Checking for analyses that are ready to run')
#        ready_analyses = get_ready_analyses(ANALYSES_URL)
#        # Run ready analyses, downloading files if needed
#        for analysis in ready_analyses:
#            for inputfile in analysis['inputfiles']:
#                download_file(inputfile)
#            run_analysis(analysis)
#        # Check status of running analyses, uploading files if done
#        for analysis in running_analyses:
#            if analysis['status'] == 'done':
#                for outputfile in analysis['outputfiles']:
#                    upload_file(outputfile)
#            update_status(analysis)

if __name__ == "__main__":
    main()

