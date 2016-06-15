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
            {'task_run': task_run})

        for output in attempt.outputs.all():
            file_data_object = cls._create_mock_file_data_object(output)
            cls._mock_upload(file_data_object)
            output.update({})

    @classmethod
    def _mock_upload(cls, data_object):
        data_object_struct = data_object.to_struct()
        data_object_struct['file_import']['temp_file_location'] = None
        data_object_struct['file_import']['file_location']['status'] = 'complete'
        data_object.update(data_object_struct)
        

    @classmethod
    def _create_mock_file_data_object(self, output):
        self.mock_file_counter += 1
        mock_text = "mock%s" % self.mock_file_counter
        mock_md5 = hashlib.md5(mock_text)
        output.update({
            'data_object': {
                'file_import': {
                    '_class': 'TaskRunAttemptOutputFileImport'
                }}})
        output.data_object.update({
            'file_content':{
                'filename': mock_text,
                'unnamed_file_content': {
                    'hash_value': mock_md5.hexdigest(),
                    'hash_function': 'md5',
                }}})
        return output.data_object
