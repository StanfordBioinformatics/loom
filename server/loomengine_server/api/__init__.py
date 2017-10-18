from . import test

# Raise a helpful error if attempting to get a setting that is missing
def get_setting(SETTING, required=True):
    from django.conf import settings
    try:
        value = getattr(settings, SETTING)
    except AttributeError:
        if required:
            raise Exception('Setting "%s" is not set' % SETTING)
        else:
            return None
    if value is None and required:
        raise Exception('Setting "%s" is not set' % SETTING)
    return value
