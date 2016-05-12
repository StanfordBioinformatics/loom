import hashlib
import requests

class DummyTaskManager(object):
    """Generate fake results for a TaskRun.
    For development use only.
    """

    dummy_file_counter = 0

    @classmethod
    def run(cls, task_run, task_run_location_id, with_error=False):

        if with_error:
            task_run.error(task_run_location_id)
        else:
            for output in task_run.task_run_outputs.all():
                data_object = cls._render_dummy_file()
                task_run.submit_result(output._id, data_object, task_run_location_id)

    @classmethod
    def _render_dummy_file(self):
        self.dummy_file_counter += 1
        dummy_text = "dummy%s" % self.dummy_file_counter
        dummy_md5 = hashlib.md5(dummy_text)
        return {
            'filename': dummy_text,
            'file_contents': {
                'hash_value': dummy_md5.hexdigest(),
                'hash_function': 'md5',
            }
        }
