#!/usr/bin/env python

import os
import subprocess
import time
from loom.master.xppfdaemon import xppf_daemon_logger

MANAGE_EXECUTABLE = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        '../manage.py'
        )
    )

SLEEP_TIME_SECONDS = 3

class App():
   
    def __init__(self, logfile=None):
        self.logfile = logfile
        self.logger = xppf_daemon_logger.get_logger(logfile)

    def run(self):
        while True:
            cmd = '%s run_job_queues' % MANAGE_EXECUTABLE
            if self.logfile:
                cmd += ' --logfile %s' % self.logfile
            retcode = subprocess.call(
                cmd,
                shell=True
                )
            self.logger.info('Running job queues')
            time.sleep(SLEEP_TIME_SECONDS)

if __name__=='__main__':
    App().run()

