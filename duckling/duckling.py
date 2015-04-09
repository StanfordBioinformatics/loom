#!/usr/bin/env python

import time
import daemon
import json
import requests

from xppf.server.apps.analysis.models import Analysis

def check_for_analyses(server_url):
    """Check the server for new analyses that are ready to run."""
    # send msg without explict analysis_id, return with todo list
    r=requests.get("http://localhost:8000/analyses", data={}, headers = {'Content-type':'application/json','Accept':'text/plain'})

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
    r=requests.post("http://localhost:8000/analyses", data=analysis_josn, headers = {'Content-type':'application/json','Accept':'text/plain'})

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
#    daemon_context = daemon.DaemonContext(
#        working_directory='.',
#        stdout=open('out.log', 'w'),
#        stderr=open('err.log', 'w')
#        )

#    with daemon_context:
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

if __name__ == "__main__":
    main()

