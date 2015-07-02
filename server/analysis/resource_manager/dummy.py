import hashlib
import requests

from analysis.models import StepResult

class DummyResourceManager:

    dummy_file_counter = 0

    @classmethod
    def run(cls, step_run):
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
            StepResult.create(result)

        #Post that run is complete
        step_run.update(
            {'is_complete': True}
            )

    @classmethod
    def _render_dummy_file(self):
        self.dummy_file_counter += 1
        dummy_text = "dummy%s" % self.dummy_file_counter
        dummy_md5 = hashlib.md5(dummy_text)
        return {
            'hash_value': dummy_md5.hexdigest(),
            'hash_function': 'md5',
            }
