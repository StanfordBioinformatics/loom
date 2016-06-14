import hashlib

from analysis.models import FileDataObject


class MockTaskManager(object):
    """Generate fake results for a TaskRun.
    For development use only.
    """

    mock_file_counter = 0

    @classmethod
    def run(cls, task_run):
        from analysis.models.task_runs import MockTaskRunAttempt
        attempt = MockTaskRunAttempt.create(
            {'task_run': task_run.to_struct()})

        for output in attempt.outputs.all():
            data_object_struct = cls._create_mock_file_data_object(output)
            cls._mock_upload(output)

    @classmethod
    def _mock_upload(cls, output):
        output.refresh_from_db()
        output_struct = output.to_struct()
        output_struct['file_location']['status'] = 'complete'
        output_struct['temp_file_location'] = None
        output.update(output_struct)

    @classmethod
    def _create_mock_file_data_object(self, output):
        self.mock_file_counter += 1
        mock_text = "mock%s" % self.mock_file_counter
        mock_md5 = hashlib.md5(mock_text)
        return FileDataObject.create(
            {
                'file_content':{
                    'filename': mock_text,
                    'unnamed_file_content': {
                        'hash_value': mock_md5.hexdigest(),
                        'hash_function': 'md5',
                    }
                },
                'file_import': output
            }
        )
