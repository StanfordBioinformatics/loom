#!/usr/bin/env python

import os
import subprocess
import sys
import time
from loom.master.loomdaemon import loom_daemon_logger

MANAGE_EXECUTABLE = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        '../manage.py'
        )
    )

SLEEP_TIME_SECONDS = 1

class App():
   
    def __init__(self, logfile=None, loglevel=None):
        self.logfile = logfile
        self.logger = loom_daemon_logger.get_logger(logfile, loglevel)

    def run(self):
        while True:
            cmd = '%s %s run_job_queues' % (sys.executable, MANAGE_EXECUTABLE)
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

