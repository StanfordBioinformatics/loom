class Error(Exception):
    pass

class DataObjectValidationError(Error):
    pass

class UnknownNameFieldError(Error):
    pass

class IdTooShortError(Error):
    pass

class InvalidIdError(Error):
    pass

class MissingInputsError(Error):
    pass

class IdNotFoundError(Error):
    pass

class TooManyMatchesError(Error):
    pass
