import hashlib

from api.models import FileDataObject


class MockTaskManager(object):
    """Generate fake results for a TaskRun.
    For testing and development use only.
    """

    mock_data_counter = 0

    @classmethod
    def run(cls, task_run):
        from api.models.task_runs import TaskRunAttempt
        attempt = TaskRunAttempt.create_from_task_run(task_run)

        for output in attempt.outputs.all():
            cls._add_mock_data(output)

        attempt.status='complete'
        attempt.save()
        attempt.after_update()
        
    @classmethod
    def _add_mock_data(cls, output):
        if output.type == 'file':
            cls._add_mock_file_data_object(output)

    @classmethod
    def _add_mock_file_data_object(self, output):
        from api.serializers import FileDataObjectSerializer

        self.mock_data_counter += 1
        mock_text = "mock%s" % self.mock_data_counter
        mock_md5 = hashlib.md5(mock_text).hexdigest()

        file_data = {
            'file_content': {
                'filename': 'mock_file_%s' % self.mock_data_counter,
                'unnamed_file_content': {
                    'hash_value': mock_md5,
                    'hash_function': 'md5'
                }
            },
            'file_location': {
                'url': 'file:///mock/location/%s' % self.mock_data_counter,
                'status': 'complete'
            }}

        s = FileDataObjectSerializer(data=file_data)
        s.is_valid(raise_exception=True)
        data_object = s.save()

        output.data_object = data_object
        output.save()

        return output.data_object
