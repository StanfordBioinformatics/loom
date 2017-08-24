from .base import BaseSettingsValidator

"""Validator for local settings
"""

class LocalSettingsValidator(BaseSettingsValidator):

    def validate(self):
        self.validate_common()
        self.raise_if_errors()

