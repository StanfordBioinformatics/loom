#!/usr/bin/env python

import logging
import os
import subprocess
import time

MANAGE_EXECUTABLE = os.path.join(
    os.path.dirname(__file__),
    '../manage.py'
    )

class App():
   
    def __init__(self):
        self._init_logger()

    def run(self):
        while True:
            retcode = subprocess.call(
                '%s run_job_queues' % MANAGE_EXECUTABLE, 
                shell=True
                )
            self.logger.info('Running job queues')
            time.sleep(5)

    def _init_logger(self):
        self.logger = logging.getLogger("AsyncLog")
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        self.handler = logging.FileHandler("/tmp/async.log")
        self.handler.setFormatter(formatter)
        self.logger.addHandler(self.handler)


if __name__=='__main__':
    App().run()

