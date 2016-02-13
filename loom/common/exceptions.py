class Error(Exception):
    pass

class ServerConnectionError(Error):
    pass

class BadResponseError(Error):
    pass

class UnrecognizedFileServerType(Error):
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
