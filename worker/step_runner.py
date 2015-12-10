#!/usr/bin/env python
from datetime import datetime
import glob
import json
import logging
import os
import errno
import requests
import string
import subprocess
import time

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from django.utils import dateparse

from loom.common import md5calc, filehandler


class InputManager:

    def __init__(self, settings, step_run, logger):
        self.settings = settings
        self.logger = logger
        self.step_run = step_run
        self.input_port_bundles = self._get_input_port_bundles()

    def _get_input_port_bundles(self):
        url = self.settings['MASTER_URL'] + '/api/step_runs/' + self.settings['RUN_ID'] + '/input_port_bundles/'
        response = requests.get(url)
        response.raise_for_status()
        input_port_bundles = response.json()['input_port_bundles']
        return input_port_bundles

    def prepare_all_inputs(self):
        if self.input_port_bundles is None:
            return
        for bundle in self.input_port_bundles:
            self._prepare_port_inputs(bundle)

    def _prepare_port_inputs(self, input_port_bundle):
        port = input_port_bundle['input_port']
        files_and_locations = input_port_bundle.get(u'files_and_locations')
        if files_and_locations is None:
            return
        for f in files_and_locations:
            self._prepare_input(f, port)

    def _prepare_input(self, file_and_locations, port):
        remote_location = file_and_locations.get('file_storage_locations')[0]
        local_path = os.path.join(self.settings['WORKING_DIR'], self._get_file_name(port))
        filehandler_obj = filehandler.FileHandler(self.settings['MASTER_URL'])
        self.logger.debug('Downloading input %s from %s' % (local_path, remote_location))
        filehandler_obj.download(remote_location, local_path)

    def _get_file_name(self, input_port):
        return input_port['file_name']


class _AbstractPortOutputManager:

    def __init__(self, settings, step_run, logger, step_definition_output_port):
        self.settings = settings
        self.step_run = step_run
        self.logger = logger
        self.output_port = step_definition_output_port

    def _get_files_by_glob(self):
        glob_string = self.output_port.get('glob')
        return glob.glob1(self.settings['WORKING_DIR'], glob_string)

    def _save_result(self, result_info):
        data = {
            'step_run': self.step_run,
            'step_result': result_info,
            }
        response = requests.post(self.settings['MASTER_URL']+'/api/submitresult', data=json.dumps(data))
        response.raise_for_status()

    def _get_location(self, file_object, file_path):
        location = {
            'file_contents': file_object['file_contents'],
            'file_path': file_path,
            'host_url': self.settings['FILE_SERVER_FOR_WORKER'],
            }
        return location

    def _get_result_info(self, data_object):
        return {
            'data_object': data_object,
            'output_port': self.output_port,
            }

class _FilePortOutputManager(_AbstractPortOutputManager):

    def process_output(self):
        file_path = self._get_file_path()
        file_object = filehandler.create_file_object(file_path)
        result_info = self._get_result_info(file_object)
        self._save_result(result_info)

        filehandler_obj = filehandler.FileHandler(self.settings['MASTER_URL'])
        location = filehandler_obj.get_step_output_location(file_path, file_object=file_object)
        self.logger.debug('Uploading output %s to %s' % (file_path, location))
        filehandler_obj.upload(file_path, location)
        filehandler.post_location(self.settings['MASTER_URL'], location)

    def _get_file_path(self):
        file_name = self.output_port.get('file_name')
        if file_name is None:
            file_names = self._get_files_by_glob()
            if len(file_names) > 1:
                raise Exception("glob pattern matched multiple files on non-array output port %s. %s" % (self.output_port['_id'], file_names))
            if len(file_names) == 0:
                raise Exception("glob pattern matched no files on non-array output port %s." % self.output_port['_id'])
            file_name = file_names[0]
        return os.path.join(
            self.settings['WORKING_DIR'],
            file_name
            )

class _FileArrayPortOutputManager(_AbstractPortOutputManager):

    def process_output(self):
        file_paths = self._get_file_paths()
        file_array = self._get_file_array_object(file_paths)
        result_info = self._get_result_info(file_array)
        self._save_result(result_info)

        filehandler_obj = filehandler.FileHandler(self.settings['MASTER_URL'])
        locations = get_locations(file_array, file_paths, filehandler_obj)
        
        for location in locations:
            filehandler.post_location(self.settings['MASTER_URL'], location)
            self.logger.debug('Uploading output %s to %s' % (file_path, location))
            filehandler_obj.upload(file_path, location)

    def get_locations(self, file_array, file_paths, filehandler_obj):
        locations = []
        for (file_object, file_path) in zip(file_array['files'], file_paths):
            locations.append(filehandler_obj.get_step_output_location(file_path, file_object))
        return locations

    def _get_file_paths(self):
        paths = []
        for file_name in self._get_files_by_glob():
            paths.append(
                os.path.join(
                    self.settings['WORKING_DIR'],
                    file_name
                    )
                )
        return paths

    def _get_files_by_glob(self):
        glob_string = self.output_port.get('glob')
        return glob.glob1(self.settings['WORKING_DIR'], glob_string)

    def _get_file_array_object(self, file_paths):
        file_array = {'files': []}
        for path in file_paths:
            file_array['files'].append(self._get_file_object(path))
        return file_array

class PortOutputManager:

    @classmethod
    def _port_manager_factory(cls, settings, step_run, logger, output_port):
        if output_port['is_array']:
            manager_class = _FileArrayPortOutputManager
        else:
            manager_class = _FilePortOutputManager
        return manager_class(settings, step_run, logger, output_port)

    @classmethod
    def process_output(cls, settings, step_run, logger, output_port):
        port_manager = cls._port_manager_factory(settings, step_run, logger, output_port)
        return port_manager.process_output()


class OutputManager:

    def __init__(self, settings, step_run, logger):
        self.settings = settings
        self.logger = logger
        self.step_run = step_run
        self.output_ports = self._get_output_ports(step_run)

    def _get_output_ports(self, step_run):
        output_ports = step_run.get('step_definition').get('output_ports')
        if output_ports is None:
            output_ports = []
        return output_ports

    def process_all_outputs(self):
        for output_port in self.output_ports:
            PortOutputManager.process_output(self.settings, self.step_run, self.logger, output_port)
        self._upload_logfiles()

    def _upload_logfiles(self):
        filehandler_obj = filehandler.FileHandler(self.settings['MASTER_URL'])
        location = filehandler_obj.get_step_output_location(self.settings['STEP_LOGFILE'])
        filehandler_obj.upload(self.settings['STEP_LOGFILE'], location)
        location = filehandler_obj.get_step_output_location(self.settings['STDOUT_LOGFILE'])
        filehandler_obj.upload(self.settings['STDOUT_LOGFILE'], location)
        location = filehandler_obj.get_step_output_location(self.settings['STDERR_LOGFILE'])
        filehandler_obj.upload(self.settings['STDERR_LOGFILE'], location)


class StepRunner:

    def __init__(self, args=None):
        if args is None:
            args=self._get_args()

        self.settings = {
            'RUN_ID': args.run_id,
            'MASTER_URL': args.master_url.rstrip('\/')
            }
        self.settings.update(self._get_additional_settings())
        self._init_logger()
        self._init_step_run()
        self.logger.debug('Initing run request')
        self._init_workflow()
        self.logger.debug('Getting working dir settings')
        self.settings.update(self._get_working_dir_setting())

        self.input_manager = InputManager(self.settings, self.step_run, self.logger)
        self.output_manager = OutputManager(self.settings, self.step_run, self.logger)

    def run(self):
        try:
            self._prepare_working_directory(self.settings['WORKING_DIR'])
            self._add_logfiles()
            self.input_manager.prepare_all_inputs()

            stdoutlog = open(self.settings['STDOUT_LOGFILE'], 'w')
            stderrlog = open(self.settings['STDERR_LOGFILE'], 'w')
            process = self._execute(stdoutlog, stderrlog)
            self._wait_for_process(process)
            stdoutlog.close()
            stderrlog.close()

            self.output_manager.process_all_outputs()
            self._flag_run_as_complete(self.step_run)

        except Exception as e:
            print e.message
            self.logger.exception(e)
            raise

    def _get_additional_settings(self):
        url = self.settings['MASTER_URL'] + '/api/workerinfo'
        response = requests.get(url)
        response.raise_for_status()
        return response.json()['workerinfo']

    def _init_step_run(self):
        url = self.settings['MASTER_URL'] + '/api/step_runs/' + self.settings['RUN_ID']
        response = requests.get(url)
        response.raise_for_status()
        self.step_run = response.json()
        self.step = self.step_run['steps'][0]
        self.logger.debug('Retrieved StepRun %s' % self.step_run)

    def _init_workflow(self):
        url = self.settings['MASTER_URL'] + '/api/run_requests'
        response = requests.get(url)
        response.raise_for_status()
        run_requests = response.json()['run_requests']
        for run_request in run_requests:
            for workflow in run_request['workflows']:
                for step in workflow['steps']:
                    if step['_id'] == self.step['_id']:
                        self.workflow = workflow
                        return
        raise Exception('Step ID not found')

    def _get_working_dir_setting(self):
        workflow_datetime_created = dateparse.parse_datetime(self.workflow['datetime_created'])
        workflow_datetime_created_string = workflow_datetime_created.strftime("%Y%m%d-%Hh%Mm%Ss")

        return {'WORKING_DIR': 
                os.path.join(
                self.settings['FILE_ROOT_FOR_WORKER'],
                'workflows',
                "%s_%s_%s" % (
                    workflow_datetime_created_string,
                    self.workflow['_id'],
                    self.workflow['name']
                    ),
                "%s_%s_%s" % (
                    datetime.now().strftime("%Y%m%d-%Hh%Mm%Ss"),
                    self.settings['RUN_ID'],
                    self.step['name']
                    )
                )
                }

    def _prepare_working_directory(self, working_dir):
        self.logger.debug('Trying to create working directory %s' % working_dir)
        try:
            os.makedirs(working_dir)
        except OSError as e:
            if e.errno == errno.EEXIST and os.path.isdir(working_dir):
                self.logger.debug('Found working directory %s' % working_dir)
            else:
                raise

    def _execute(self, stdoutlog, stderrlog):
        step_definition = self.step_run.get('step_definition')
        environment = step_definition.get('environment')
        docker_image = environment.get('docker_image')
        user_command = step_definition.get('command')
        host_dir = self.settings['WORKING_DIR']
        container_dir = '/working_dir'
        raw_full_command = 'docker run --rm -v ${host_dir}:${container_dir}:rw -w ${container_dir} $docker_image sh -c \'$user_command\'' #TODO - need sudo?
        full_command = string.Template(raw_full_command).substitute(container_dir=container_dir, host_dir=host_dir, docker_image=docker_image, user_command=user_command)
        self.logger.debug(full_command)
        return subprocess.Popen(full_command, shell=True, stdout=stdoutlog, stderr=stderrlog)

    def _wait_for_process(self, process, poll_interval_seconds=1, timeout_seconds=86400):
        start_time = datetime.now()
        while True:
            time_running = datetime.now() - start_time
            if time_running.seconds > timeout_seconds:
                raise Exception("Timeout")
            returncode = process.poll()
            if returncode is not None:
                break
            time.sleep(poll_interval_seconds)
        if returncode == 0:
            return
        else:
            raise Exception('Process returned with error %s' % str(returncode))

    def _flag_run_as_complete(self, step_run):
        update_data = {'are_results_complete': True, 'is_running': False}
        url = self.settings['MASTER_URL']+'/api/step_runs/%s' % step_run.get('_id')
        self.logger.debug('updating StepRun at url '+url)
        response = requests.post(url, data=json.dumps(update_data))
        response.raise_for_status()

    def _get_args(self):
        parser = self._get_parser()
        args = parser.parse_args()
        return args

    @classmethod
    def _get_parser(cls):
        import argparse
        parser = argparse.ArgumentParser('step_runner')
        parser.add_argument('--run_id', '-i',
                            help="ID of step run to be executed",
                            required=True)
        parser.add_argument('--master_url', '-m',
                            help="URL of master server",
                            required=True)
        return parser

    def _init_logger(self):
        self.logger = logging.getLogger("LoomWorker")
        self.logger.setLevel(self.settings['LOG_LEVEL'])
        formatter = logging.Formatter('%(levelname)s [%(asctime)s] %(message)s')
        handler = self._init_handler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _init_handler(self):
        if self.settings.get('WORKER_LOGFILE') is None:
            return logging.StreamHandler()
        else:
            if not os.path.exists(os.path.dirname(self.settings['WORKER_LOGFILE'])):
                os.makedirs(os.path.dirname(self.settings['WORKER_LOGFILE']))
            return logging.FileHandler(self.settings['WORKER_LOGFILE'])

    def _add_logfiles(self):
        """Add logfiles for the worker, stdout, and stderr."""
        self.settings.update({'STEP_LOGFILE': os.path.join(self.settings['WORKING_DIR'], 'worker_log.txt')})
        self.settings.update({'STDOUT_LOGFILE': os.path.join(self.settings['WORKING_DIR'], 'stdout_log.txt')})
        self.settings.update({'STDERR_LOGFILE': os.path.join(self.settings['WORKING_DIR'], 'stderr_log.txt')})

        formatter = logging.Formatter('%(levelname)s [%(asctime)s] %(message)s')
        handler = logging.FileHandler(self.settings['STEP_LOGFILE'])
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        

class StepRunnerError(Exception):
    pass


if __name__=='__main__':
    StepRunner().run()
