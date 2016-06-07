import hashlib


class MockTaskManager(object):
    """Generate fake results for a TaskRun.
    For development use only.
    """

    mock_file_counter = 0

    @classmethod
    def run(cls, task_run):
        from analysis.models.task_runs import MockTaskRunExecution
        MockTaskRunExecution.create({'task_run': task_run.to_struct()})

        for output in task_run.outputs.all():
            data_object = cls._render_mock_file_data_object()
            output.update({'data_object': data_object})
        print task_run.task_definition.command

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
