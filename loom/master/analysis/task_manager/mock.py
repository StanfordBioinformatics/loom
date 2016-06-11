import hashlib


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
            data_object = cls._render_mock_file_data_object()
            cls._mock_upload(output, data_object)

    @classmethod
    def _mock_upload(cls, output, data_object):
        output.update({'data_object': data_object})
        file_location = output.file_location.to_struct()
        file_location.update({'status': 'complete'})
        output.update({'file_location': file_location})

    @classmethod
    def _render_mock_file_data_object(self):
        self.mock_file_counter += 1
        mock_text = "mock%s" % self.mock_file_counter
        mock_md5 = hashlib.md5(mock_text)
        return {
            'file_content':{
                'filename': mock_text,
                'unnamed_file_content': {
                    'hash_value': mock_md5.hexdigest(),
                    'hash_function': 'md5',
                }
            }
        }
