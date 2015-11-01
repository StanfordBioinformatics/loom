#!/usr/bin/env python

import logging
import os
import subprocess
import time

MANAGE_EXECUTABLE = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        '../manage.py'
        )
    )

SLEEP_TIME_SECONDS = 3

class App():
   
    def __init__(self, logfile=None):
        self._init_logger(logfile)

    def run(self):
        while True:
            retcode = subprocess.call(
                '%s run_job_queues' % MANAGE_EXECUTABLE, 
                shell=True
                )
            self.logger.info('Running job queues')
            time.sleep(SLEEP_TIME_SECONDS)

    def _init_logger(self, logfile):
        self.logger = logging.getLogger("XppfDaemon")
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(levelname)s [%(asctime)s] %(message)s')
        handler = self._init_handler(logfile)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _init_handler(self, logfile):
        if logfile is None:
            return logging.StreamHandler()
        else:
            if not os.path.exists(os.path.dirname(logfile)):
                os.makedirs(os.path.dirname(logfile)) 
            return logging.FileHandler(logfile)

if __name__=='__main__':
    App().run()

