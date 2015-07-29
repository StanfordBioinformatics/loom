#!/usr/bin/env python
from datetime import datetime
import requests
import string
import subprocess
import time

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

    def _get_outputs(self, step_run):
        #TODO
        return []

    def run(self):
        step_run = self._get_step_run()
        inputs = self._get_input_port_bundles().get('input_port_bundles')
        outputs = self._get_outputs(step_run)

        self._prepare_inputs(inputs)
        process = self._execute(step_run)
        self._wait_for_process(process)
        self._process_outputs(outputs)
        self._save_results()

    def _prepare_inputs(self, inputs):
        if inputs is None:
            return
        for input in inputs:
            self.prepate_input(input)

    def _prepare_input(input):
        #TODO
        pass

    def _execute(self, step_run):
        step_definition = step_run.get('step_definition')
        template = step_definition.get('template')
        environment = template.get('environment')
        docker_image = environment.get('docker_image')
        command = template.get('command')
        working_dir = '~/working_dir' #TODO
        cmd_template = string.Template('docker run --rm -v ${working_dir}:/working_dir -w /working_dir $docker_image sh -c \'$command\'') #TODO - need sudo?
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

    def _process_outputs(self, outputs):
        for output in outputs:
            self.process_otuput(output)
    
    def _process_output(self, output):
        # TODO
        pass

    def _save_results(self):
        #TODO
        pass

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
