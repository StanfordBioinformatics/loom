class LoomengineUtilsError(Exception):
    pass

class APIError(LoomengineUtilsError):
    pass

class ServerConnectionError(LoomengineUtilsError):
    pass

class ServerConnectionHttpError(ServerConnectionError):

    def __init__(self, message, status_code=None, **kwargs):
        super(ServerConnectionHttpError, self).__init__(message, **kwargs)
        self.status_code = status_code

class ResourceCountError(LoomengineUtilsError):
    pass

class ExportManagerError(LoomengineUtilsError):
    pass

class FileAlreadyExistsError(ExportManagerError):
    pass

class FileUtilsError(LoomengineUtilsError):
    pass

class Md5ValidationError(FileUtilsError):
    pass

class UrlValidationError(FileUtilsError):
    pass

class InvalidYamlError(FileUtilsError):
    pass

class NoFileError(FileUtilsError):
    pass

class ImportManagerError(LoomengineUtilsError):
    pass

class FileDuplicateError(ImportManagerError):
    pass
