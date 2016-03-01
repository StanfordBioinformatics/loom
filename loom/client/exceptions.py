class Error(Exception):
    pass

class UploadException(Error):
    pass

class NotAFileError(Error):
    pass

class NoFilesFoundError(Error):
    pass

class InvalidFileNameError(Error):
    pass

class InvalidInputError(Error):
    pass

class DestinationDirectoryNotFoundError(Error):
    pass

class ArgumentError(Error):
    pass

class ValidationError(Error):
    pass

class NoFileError(Error):
    pass

class InvalidFormatError(Error):
    pass

class UnmatchedInputError(Error):
    pass

class IdMatchedTooFewFileDataObjectsError(Error):
    pass

class IdMatchedTooManyFileDataObjectsError(Error):
    pass

class IdDoesNotMatchError(Error):
    pass
