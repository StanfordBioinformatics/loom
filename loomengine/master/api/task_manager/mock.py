import hashlib

from api.models import DataObject


class MockTaskManager(object):
    """Generate fake results for a TaskRun.
    For testing and development use only.
    """

    mock_data_counter = 0

    @classmethod
    def run(cls, task):
        from api.models.tasks import TaskAttempt
        attempt = TaskAttempt.create_from_task(task)

        for output in attempt.outputs.all():
            cls._add_mock_data(output)

        attempt.status='complete'
        attempt.save()
        
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
            'type': 'file',
            'filename': 'mock_file_%s' % self.mock_data_counter,
            'md5': mock_md5,
            'source_type': 'result'}

        s = FileDataObjectSerializer(data=file_data)
        s.is_valid(raise_exception=True)
        data_object = s.save()

        output.data_object = data_object
        output.save()

        return output.data_object
