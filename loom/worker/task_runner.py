#!/usr/bin/env python

import argparse
import copy
from datetime import datetime
import errno
import logging
import os
import requests
import string
import subprocess
import sys
import time
import uuid

from loom.common.filehandler import FileHandler
from loom.common.objecthandler import ObjectHandler
from loom.common.logger import StreamToLogger

class TaskRunner(object):

    def __init__(self, args=None):
        if args is None:
            args = self._get_args()
        self.settings = {
            'TASK_RUN_ATTEMPT_ID': args.run_attempt_id,
            'MASTER_URL': args.master_url
        }
        self._init_objecthandler()
        self.settings.update(self._get_worker_settings())
        self._init_directories()
        self._init_logger()
        self._init_filehandler()
        self._init_task_run_attempt()

    def _init_objecthandler(self):
        self.objecthandler = ObjectHandler(self.settings['MASTER_URL'])

    def _init_filehandler(self):
        self.filehandler = FileHandler(self.settings['MASTER_URL'], logger=self.logger)

    def _get_worker_settings(self):
        return self.objecthandler.get_worker_settings(self.settings['TASK_RUN_ATTEMPT_ID'])

    def _init_directories(self):
        for directory in set([self.settings['WORKING_DIR'],
                              os.path.dirname(self.settings['WORKER_LOG_FILE']),
                              os.path.dirname(self.settings['STDOUT_LOG_FILE']),
                              os.path.dirname(self.settings['STDERR_LOG_FILE']),
        ]):
            try:
                if not os.path.exists(directory):
                    os.makedirs(directory)
            except OSError as e:
                raise Exception('Failed to create directory %s. %s' % (directory, e.strerror))

    def _init_logger(self):
        self.logger = logging.getLogger("LoomWorker")
        self.logger.setLevel(self.settings['LOG_LEVEL'])
        self.logger.raiseExceptions = True
        formatter = logging.Formatter('%(levelname)s [%(asctime)s] %(message)s')
        handler = self._init_handler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        stdout_logger = StreamToLogger(self.logger, logging.INFO)
        sys.stdout = stdout_logger
        stderr_logger = StreamToLogger(self.logger, logging.ERROR)
        sys.stderr = stderr_logger

    def _init_handler(self):
        if self.settings.get('WORKER_LOG_FILE') is None:
            return logging.StreamHandler()
        else:
            if not os.path.exists(os.path.dirname(self.settings['WORKER_LOG_FILE'])):
                os.makedirs(os.path.dirname(self.settings['WORKER_LOG_FILE']))
            return logging.FileHandler(self.settings['WORKER_LOG_FILE'])

    def _init_task_run_attempt(self):
        self.task_run_attempt = self.objecthandler.get_task_run_attempt(self.settings['TASK_RUN_ATTEMPT_ID'])
        if self.task_run_attempt is None:
            raise Exception('TaskRunAttempt ID "%s" not found' % self.settings['TASK_RUN_ATTEMPT_ID'])

    def run(self):
        self._export_inputs()

        with open(self.settings['STDOUT_LOG_FILE'], 'w') as stdoutlog:
            with open(self.settings['STDERR_LOG_FILE'], 'w') as stderrlog:
                process = self._execute(stdoutlog, stderrlog)
                self._wait_for_process(process)

        if process.returncode == 0:
            self._import_outputs()
            self._import_log_files()
            self._flag_attempt_as_complete()
        else:
            err_message = 'Worker process failed with nonzero returncode %s. \nFor more '\
                          'information check the stderr log file' % str(process.returncode)
            self.logger.error(err_message)
            # TODO report failure to server

            # Still report output for debugging purposes
            self._import_outputs()
            self._import_log_files()

    def _flag_attempt_as_complete(self):
        task_run_attempt = copy.deepcopy(self.task_run_attempt)
        task_run_attempt.update({'status': 'complete'})
        
        self.objecthandler.update_task_run_attempt(
            task_run_attempt['id'],
            task_run_attempt)
        
    def _export_inputs(self):
        if self.task_run_attempt.get('inputs') is None:
            return
        file_data_object_ids = []
        for input in self.task_run_attempt['inputs']:
            if input['data_object']['type'] == 'file':
                file_data_object_ids.append('@'+input['data_object']['id'])
        self.filehandler.export_files(
            file_data_object_ids,
            destination_url=self.settings['WORKING_DIR'])

    def _import_outputs(self):
        for output in self.task_run_attempt['outputs']:
            if output['type'] == 'file':
                filename = output['filename']
                try:
                    self.filehandler.import_result_file(
                        output,
                        os.path.join(self.settings['WORKING_DIR'], filename)
                    )
                except IOError:
                    self.logger.error('Failed to upload output file %s' % filename)
                    # TODO report failure due to missing file
                    # Catch error to continue uploading other files
            else:
                # TODO handle non-file output types
                raise Exception("Can't handle outputs of type %s" %
                                output['type'])

    def _import_log_files(self):
        for log_file in (self.settings['WORKER_LOG_FILE'],
                        self.settings['STDOUT_LOG_FILE'],
                        self.settings['STDERR_LOG_FILE']):
            try:
                self.filehandler.import_log_file(
                    self.task_run_attempt,
                    log_file
                )
            except IOError:
                self.logger.error('Failed to upload log file %s' % filename)

    def _execute(self, stdoutlog, stderrlog):
        task_definition = self.task_run_attempt['task_definition']
        environment = task_definition['environment']
        docker_image = environment['docker_image']
        user_command = task_definition['command']
        host_dir = self.settings['WORKING_DIR']
        container_dir = '/working_dir'
        
        full_command = [
            'docker',
            'run',
            '--rm',
            '-v',
            '%s:%s:rw' % (host_dir, container_dir),
            '-w',
            container_dir,
            docker_image,
            'bash',
            '-o',
            'pipefail',
            '-c',
            user_command,
            ]
        self.logger.debug(' '.join(full_command))
        return subprocess.Popen(full_command, stdout=stdoutlog, stderr=stderrlog)

    def _wait_for_process(self, process, poll_interval_seconds=1, timeout_seconds=86400):
        start_time = datetime.now()
        while True:
            time_running = datetime.now() - start_time
            if time_running.seconds > timeout_seconds:
                raise Exception("Timeout")
            returncode = process.poll()
            if returncode is not None:
                return
            time.sleep(poll_interval_seconds)

    def _get_args(self):
        parser = self.get_parser()
        return parser.parse_args()

    @classmethod
    def get_parser(self):
        parser = argparse.ArgumentParser(__file__)
        parser.add_argument('--run_attempt_id',
                            '-i',
                            required=True,
                            help='ID of TaskRunAttempt to be processed')
        parser.add_argument('--master_url',
                            '-u',
                            required=True,
                            help='URL of the Loom master server')
        return parser


# pip entrypoint requires a function with no arguments 
def main():
    TaskRunner().run()

if __name__=='__main__':
    main()
