#!/usr/bin/env python3

import time
import daemon

def check_for_analyses(server_url):
    """Check the server for new analyses that are ready to run."""

def get_anlysis(analysis_id):
    """Get full JSON specifying the named analysis."""

def run_analysis(analysis):
    """Run the analysis."""

def update_status(server_url):
    """Update the server with the current status of each analysis? all analyses?"""

def download_file(file_info):

def upload_file(file_info):

def main():
    """Runs as a detached process, writing stdout and stderr to log files in the current directory."""
    daemon_context = daemon.DaemonContext(
        working_directory='.',
        stdout=open('out.log', 'w'),
        stderr=open('err.log', 'w')
        )

    with daemon_context:
        while(True):
            time.sleep(5)   
            print('hi')

if __name__ == "__main__":
    main()
