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
from xppf.common import md5calc


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
        cmd = ['ln',
               self._select_location(file_and_locations.get('file_storage_locations')),
               self._get_file_name(port)]
        subprocess.call(cmd, cwd=self.settings['WORKING_DIR'])

    def _get_file_name(self, input_port):
        return input_port['file_name']

    def _select_location(self, locations):
        return locations[0]['file_path']

class _AbstractPortOutputManager:

    def __init__(self, settings, step_run, logger, output_port):
        self.settings = settings
        self.step_run = step_run
        self.logger = logger
        self.output_port = output_port

    def _get_files_by_glob(self):
        glob_string = self.output_port.get('glob')
        return glob.glob1(self.settings['WORKING_DIR'], glob_string)

    def _get_file_object(self, file_path):
        file = {
            'file_contents': {
                'hash_value': md5calc.calculate_md5sum(file_path),
                'hash_function': 'md5',
                }
            }
        return file

    def _save_result(self, result):
        data = {
            'step_run': self.step_run,
            'step_result': result,
            }
        response = requests.post(self.settings['MASTER_URL']+'/api/submitresult', data=json.dumps(data))
        response.raise_for_status()

    def _save_location(self, location):
        response = requests.post(self.settings['MASTER_URL']+'/api/file_storage_locations', data=json.dumps(location))
        response.raise_for_status()

    def _get_location(self, file_object, file_path):
        location = {
            'file_contents': file_object['file_contents'],
            'file_path': file_path,
            'host_url': self.settings['FILE_SERVER_FOR_WORKER'],
            }
        return location

    def _get_result(self, data_object):
        return {
            'step_definition': self.step_run['step_definition'],
            'output_binding': {
                'data_object': data_object,
                'output_port': self.output_port,
                },
            }

class _FilePortOutputManager(_AbstractPortOutputManager):

    def process_output(self):
        file_path = self._get_file_path()
        file_object = self._get_file_object(file_path)
        result = self._get_result(file_object)
        location = self._get_location(file_object, file_path)
        self._save_result(result)
        self._save_location(location)

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
        result = self._get_result(file_array)
        self._save_result(result)
        locations = self._get_locations(file_array, file_paths)
        for location in locations:
            self._save_location(location)

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

    def _get_locations(self, file_array, file_paths):
        locations = []
        for (file_object, file_path) in zip(file_array['files'], file_paths):
            locations.append(self._get_location(file_object, file_path))
        return locations


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
        output_ports = step_run.get('step_definition').get('template').get('output_ports')
        if output_ports is None:
            output_ports = []
        return output_ports

    def process_all_outputs(self):
        for output_port in self.output_ports:
            PortOutputManager.process_output(self.settings, self.step_run, self.logger, output_port)


class StepRunner:

    STEP_RUNS_DIR = 'step_runs'

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
        self.settings.update(self._get_working_dir_setting())

        self.input_manager = InputManager(self.settings, self.step_run, self.logger)
        self.output_manager = OutputManager(self.settings, self.step_run, self.logger)

    def run(self):
        try:
            self._prepare_working_directory(self.settings['WORKING_DIR'])
            self.input_manager.prepare_all_inputs()

            process = self._execute()
            self._wait_for_process(process)

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
        self.logger.debug('Retrieved StepRun %s' % self.step_run)

    def _get_working_dir_setting(self):
        return {'WORKING_DIR': 
                os.path.join(
                self.settings['FILE_ROOT'],
                self.STEP_RUNS_DIR,
                "%s_%s" % (
                    datetime.now().strftime("%Y%m%d-%Hh%Mm%Ss"),
                    self.settings['RUN_ID']
                    )
                )
                }

    def _prepare_working_directory(self, working_dir):
        try:
            os.makedirs(working_dir)
            self.logger.debug('Created working directory %s' % working_dir)
        except OSError as e:
            if e.errno == errno.EEXIST and os.path.isdir(working_dir):
                self.logger.debug('Found working directory %s' % working_dir)
            else:
                raise

    def _execute(self):
        step_definition = self.step_run.get('step_definition')
        template = step_definition.get('template')
        environment = template.get('environment')
        docker_image = environment.get('docker_image')
        user_command = template.get('command')
        host_dir = self.settings['WORKING_DIR']
        container_dir = '/working_dir'
        raw_full_command = 'docker run --rm -v ${host_dir}:${container_dir}:rw -w ${container_dir} $docker_image sh -c \'$user_command\'' #TODO - need sudo?
        full_command = string.Template(raw_full_command).substitute(container_dir=container_dir, host_dir=host_dir, docker_image=docker_image, user_command=user_command)
        self.logger.debug(full_command)
        return subprocess.Popen(full_command, shell=True)

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
        update_data = {'is_complete': True}
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
        self.logger = logging.getLogger("XppfWorker")
        self.logger.setLevel(self.settings['LOG_LEVEL'])
        formatter = logging.Formatter('%(levelname)s [%(asctime)s] %(message)s')
        handler = self._init_handler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _init_handler(self):
        if self.settings.get('WORKER_LOGFILE') is None:
            return logging.StreamHandler()
        else:
            return logging.FileHandler(self.settings['WORKER_LOGFILE'])


if __name__=='__main__':
    StepRunner().run()
