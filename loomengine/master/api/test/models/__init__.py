from api.models import StringDataObject

def _get_string_data_object(text):
    return StringDataObject.objects.create(
        type='string',
        value=text
    )
