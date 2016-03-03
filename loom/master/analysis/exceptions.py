class Error(Exception):
    pass

class DataObjectValidationError(Error):
    pass

class UnknownNameFieldError(Error):
    pass

class IdTooShortError(Error):
    pass

class MissingInputsError(Error):
    pass
