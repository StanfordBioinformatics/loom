#!/usr/bin/env python

"""Pipeline runner. Stays running, wakes up every specified time interval, gets analyses from the server, downloads input files,
runs analyses, uploads output files, and updates the server with analysis status.

If DAEMON = True, runs as a detached process, writing stdout and stderr to log files in the current directory.
"""

import time
import json
import logging
import requests
import daemon

from xppf.server.apps.analysis.models import Analysis

DAEMON = False
SLEEP_TIME = 5
SERVER_URL = 'http://localhost:8000'
ANALYSES_URL = SERVER_URL + '/analyses'
STATUS_URL = SERVER_URL + '/status'

def check_server_status(status_url):
    r=requests.get(status_url)
    print(r)

def get_ready_analyses(server_url):
    """Check the server for new analyses that are ready to run."""
    # send msg without explict analysis_id, return with todo list
    r=requests.get(server_url, data={}, headers = {'Content-type':'application/json','Accept':'text/plain'})
    print(r)

def get_analysis(analysis_id):
    """Get full JSON specifying the named analysis."""
    # send msg with explict analysis_id, return analysis description in json format
    todo_analysis_ids = []
    query={}
    if(analysis_id is None):
        r=requests.get("http://localhost:8000/analyses", data={}, headers = {'Content-type':'application/json','Accept':'text/plain'})
        query = json.loads( r.text.replace("\\","").replace("]\"","]").replace('\"[',"[") )
        for q in query:
            todo_analysis_ids.append(q['fields']['analysis'])
    else:
        data_pkg = json.dumps({'analysis_id':analysis_id})
        r=requests.get("http://localhost:8000/analyses", data=data_pkg, headers = {'Content-type':'application/json','Accept':'text/plain'})
        query = json.loads( r.text.replace("\\","").replace("]\"","]").replace('\"[',"[") )
    return query

def run_analysis(analysis):
    """Run the analysis."""
    analysis_json = json.loads(open("analysis_demo.json").read())
    r=requests.post(SERVER_URL, data=analysis_josn, headers = {'Content-type':'application/json','Accept':'text/plain'})

def update_status(server_url):
    """Update the server with the current status of each analysis? all analyses?"""
    analysis_id = "93eef400-ddb5-11e4-ab2d-60f81dd0008a"
    status_data = '{"analysis_id":"'+analysis_id+'","server":"localhost"}'
    r=requests.post("http://localhost:8000/"+analysis_id, data={}, headers = {'Content-type':'application/json','Accept':'text/plain'})

def download_file(file_info):
    msg=''

def upload_file(file_info):
    msg=''

def main():
    """Runs as a detached process, writing stdout and stderr to log files in the current directory."""
    if DAEMON:
        daemon_context = daemon.DaemonContext(
            working_directory='.',
            stdout=open('out.log', 'w'),
            stderr=open('err.log', 'w')
            )
        daemon_context.open()

    while(True):
        analysis_ids = get_analysis(None)
        print( "#"+str(analysis_ids)+" of analyses in the todo list" )
        for analysis_entry in analysis_ids:
            #Execute the analysis
            analysis_id = get_analysis(analysis_entry['fields']['analysis'])
            print("\n***analyze:"+str(analysis_id))
            analysis = Analysis.objects.get(analysisid=analysis_id)
            for step in analysis.steps:
                print("\n>>>STEP:"+str(step))
            #update_analysis(analysis_id)
        time.sleep(1) 
        print('hi')

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

