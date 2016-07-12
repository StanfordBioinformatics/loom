from . import test

def get_setting(SETTING):
    from django.conf import settings
    try:
        value = getattr(settings, SETTING)
    except AttributeError:
        raise Exception('Setting "%s" is not set' % SETTING)
    if value is None:
        raise Exception('Setting "%s" is not set' % SETTING)
    return value

