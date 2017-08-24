class SettingsValidationError(Exception):
    pass

def validate(settings, LOOM_SETTINGS_VALIDATOR):
    if not LOOM_SETTINGS_VALIDATOR:
        return
    if not LOOM_SETTINGS_VALIDATOR in VALIDATORS:
        raise SettingsValidationError(
            'Unsupported value for LOOM_SETTINGS_VALIDATOR "%s". '\
            'Choose from "%s"'
            % (LOOM_SETTINGS_VALIDATOR, '", "'.join(VALIDATORS.keys())))

    Validator = VALIDATORS[LOOM_SETTINGS_VALIDATOR]
    Validator(settings).validate()

from .local import LocalSettingsValidator
from .gcloud import GcloudSettingsValidator

VALIDATORS = {
    'local': LocalSettingsValidator,
    'gcloud': GcloudSettingsValidator,
}
