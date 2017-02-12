import hashlib

from api.models import DataObject, FileDataObject, StringDataObject, \
    BooleanDataObject, FloatDataObject, IntegerDataObject


class MockTaskManager(object):
    """Generate fake results for a TaskRun.
    For testing and development use only.
    """

    mock_data_counter = 0

    @classmethod
    def run(cls, task_attempt):
        task_attempt.status = 'RUNNING'
        task_attempt.save()

        # import time
        # time.sleep(20)
        
        for output in task_attempt.outputs.all():
            cls._add_mock_data(output)

        task_attempt.status = 'FINISHED'
        task_attempt.save()

    @classmethod
    def _add_mock_data(cls, output):
        cls.mock_data_counter += 1

        if output.type == 'file':
            return cls._add_mock_file_data_object(output)

        if output.type == 'string':
            value = 'string'+str(cls.mock_data_counter)
            DataObjectClass = StringDataObject
        elif output.type == 'integer':
            value = cls.mock_data_counter
            DataObjectClass = IntegerDataObject
        elif output.type == 'float':
            value = float(cls.mock_data_counter)/7
            DataObjectClass = FloatDataObject
        elif output.type == 'boolean':
            value = bool(cls.mock_data_counter % 2)
            DataObjectClass = BooleanDataObject
        else:
            raise Exception(
                'The mock task manager cannot handle type %s' % output.type)
        cls._add_mock_data_object(output, DataObjectClass, value)

    @classmethod
    def _add_mock_file_data_object(cls, output):
        mock_text = "mock%s" % cls.mock_data_counter
        mock_md5 = hashlib.md5(mock_text).hexdigest()

        file_data = {
            'type': 'file',
            'filename': 'mock_file_%s' % cls.mock_data_counter,
            'md5': mock_md5,
            'source_type': 'result',
        }
        file_data_object = FileDataObject.objects.create(**file_data)
        output.data_object = file_data_object
        output.save()
        file_data_object.initialize()
        file_data_object.save()
        file_data_object.file_resource.upload_status = 'complete'
        file_data_object.file_resource.save()
        return file_data_object

    @classmethod
    def _add_mock_data_object(cls, output, DataObjectClass, value):
        data = {
            'type': output.type,
            'value': value
        }
        data_object = DataObjectClass.objects.create(**data)
        output.data_object = data_object
        output.save()
        return data_object
