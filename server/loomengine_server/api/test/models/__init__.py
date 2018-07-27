from api.models import DataObject, DataNode

def _get_string_data_object(text):
    return DataObject.objects.create(
        type='string',
        data={'value': text}
    )

def _get_string_data_node(value):
    if isinstance(value, (str, unicode)):
        data_object = _get_string_data_object(value)
        data_node = DataNode.objects.create(type='string')
        data_node.add_data_object([], data_object, save=True)
    else:
        assert isinstance(value, (list, tuple))
        data_node = DataNode.objects.create(type='string')
        for i in range(len(value)):
            data_object = _get_string_data_object(value[i])
            data_node.add_data_object([(i, len(value))], data_object, save=True)
    return data_node
