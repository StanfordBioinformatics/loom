#!/usr/bin/env python
from datetime import datetime
import json
import os
import requests
import string
import subprocess
import time

from xppf.utils import md5calc

class DataNotFoundException(Exception):
    pass

class StepRunner:

    def __init__(self, args=None):
        if args is None:
            args=self._get_args()

        self.RUN_ID = args.run_id
        self.MASTER_URL = args.master_url.rstrip('\\')
        self.FILE_SERVER = args.file_server
        self.FILE_ROOT = args.file_root

    def _get_step_run(self):
        url = self.MASTER_URL + '/api/step_runs/' + self.RUN_ID
        response = requests.get(url)
        if not response.status_code == 200:
            raise DataNotFoundException("Step run not found at url %s" % url)
        step_run = response.json()
        return step_run

    def _get_input_port_bundles(self):
        url = self.MASTER_URL + '/api/step_runs/' + self.RUN_ID + '/input_port_bundles/'
        response = requests.get(url)
        if not response.status_code == 200:
            raise DataNotFoundException("Input port bundles not found at url %s" % url)
        input_port_bundles = response.json()
        return input_port_bundles

    def _get_output_ports(self, step_run):
        output_ports = step_run.get('step_definition').get('template').get('output_ports')
        if output_ports is None:
            output_ports = []
        return output_ports

    def run(self):
        step_run = self._get_step_run()
        inputs = self._get_input_port_bundles().get('input_port_bundles')
        output_ports = self._get_output_ports(step_run)

        self._prepare_inputs(inputs)
        process = self._execute(step_run)
        self._wait_for_process(process)

        results = self._process_outputs(output_ports, step_run.get('step_definition'))
        self._save_results(results, step_run)

    def _prepare_inputs(self, inputs):
        if inputs is None:
            return
        for input in inputs:
            self._prepare_input(input)

    def _prepare_input(self, input):
        #TODO
        pass

    def _execute(self, step_run):
        step_definition = step_run.get('step_definition')
        template = step_definition.get('template')
        environment = template.get('environment')
        docker_image = environment.get('docker_image')
        command = template.get('command')
        working_dir = self.FILE_ROOT #TODO - move into dirs by run, step
        cmd_template = string.Template('docker run --rm -v /working_dir:${working_dir} -w /working_dir $docker_image sh -c \'$command\'') #TODO - need sudo?
        cmd = cmd_template.substitute(working_dir=working_dir, docker_image=docker_image, command=command)
        return subprocess.Popen(cmd, shell=True)

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

    def _process_outputs(self, output_ports, step_definition):
        results = []
        for output_port in output_ports:
            results.append(self._process_output(output_port, step_definition))
        return results

    def _process_output(self, output_port, step_definition):
        result = {
            'step_definition': step_definition,
            'output_binding': {
                'file': self._get_file_obj(
                    os.path.join(
                        self.FILE_ROOT,
                        output_port.get('file_path')
                        )
                    ),
                'output_port': output_port,
                },
            }
        return result

    def _get_file_obj(self, file_path):
        file = {
            'hash_value': md5calc.calculate_md5sum(file_path),
            'hash_function': 'md5',
            }
        return file

    def _save_results(self, results, step_run):
        for result in results:
            self._save_result(result, step_run)

    def _save_result(self, result, step_run):
        data = {
            'step_run': step_run,
            'step_result': result,
            }
        requests.post(self.MASTER_URL+'/api/submitresult', data=json.dumps(data))
        # TODO verify

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
        parser.add_argument('--file_server', '-f',
                            help="Hostname of file server. Used in recording results file locations.",
                            required=True)
        parser.add_argument('--file_root', '-r',
                            help="Local path to root of working directories",
                            required=True)
        return parser

if __name__=='__main__':
    # step_runner.py --run_id {RUN_ID} --server_url {URL} --file_server {FILE_SERVER} --file_root {FILE_ROOT}
    StepRunner().run()
