class LoomengineUtilsError(Exception):
    pass

class APIError(LoomengineUtilsError):
    pass

class ServerConnectionError(LoomengineUtilsError):
    pass

class ServerConnectionHttpError(ServerConnectionError):
    def __init__(self, http_error):
        super(ServerConnectionError, self).__init__(http_error)
        self.request = http_error.request
        self.response = http_error.response
        self.message = http_error.response.text

class ResourceCountError(LoomengineUtilsError):
    pass

class ExportManagerError(LoomengineUtilsError):
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
