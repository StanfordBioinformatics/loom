def to_bool(value):
    if value and value.lower() in ['true', 't', 'yes', 'y']:
        return True
    else:
        return False

from .validator import SettingsValidator

def validate(settings):
    SettingsValidator(settings).validate()
