from api.models import DataObject

def _get_string_data_object(text):
    return DataObject.objects.create(
        type='string',
        data={'value': text}
    )
