class Error(Exception):
    pass

class ServerConnectionError(Error):
    pass

class BadResponseError(Error):
    pass

class UnrecognizedFileServerTypeError(Error):
    pass

class UndefinedFileIDError(Error):
    pass

class ObjectNotFoundError(Error):
    pass

class AbsolutePathInFileNameError(Error):
    pass

class WrongNumberOfFileNamesError(Error):
    pass

class FileAlreadyExistsError(Error):
    pass

class NoFilesMatchError(Error):
    pass

class MultipleFilesMatchError(Error):
    pass

class IdMatchedTooFewDataObjectsError(Error):
    pass

class IdMatchedTooManyDataObjectsError(Error):
    pass
    
class ValidationError(Error):
    pass
