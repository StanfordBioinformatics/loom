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
