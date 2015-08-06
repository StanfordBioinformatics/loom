import hashlib
import requests

from analysis.models import StepResult


class DummyWorkerManager:

    dummy_file_counter = 0

    @classmethod
    def run(cls, step_run):
        from analysis.models.work_in_progress import WorkInProgress
        # Generate a result,
        # post it to the web server.

        for output_port in step_run.step_definition.template.output_ports.all():

            result = {
                'step_definition': step_run.step_definition.to_obj(),
                'output_binding': {
                    'file': cls._render_dummy_file(),
                    'output_port': output_port.to_obj(),
                    },
                }

            # Post result
            WorkInProgress.submit_result({'step_run': step_run.to_json(), 'step_result': result})

        #Remove run from queue
        WorkInProgress.close_run(step_run.to_json())

    @classmethod
    def _render_dummy_file(self):
        self.dummy_file_counter += 1
        dummy_text = "dummy%s" % self.dummy_file_counter
        dummy_md5 = hashlib.md5(dummy_text)
        return {
            'hash_value': dummy_md5.hexdigest(),
            'hash_function': 'md5',
            }
