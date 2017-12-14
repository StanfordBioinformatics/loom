class LoomengineUtilsError(Exception):
    pass

class ServerConnectionError(LoomengineUtilsError):
    pass

class ResourceCountError(LoomengineUtilsError):
    pass

class UnrecognizedFileServerTypeError(LoomengineUtilsError):
    pass

class UndefinedFileIDError(LoomengineUtilsError):
    pass

class ObjectNotFoundError(LoomengineUtilsError):
    pass

class AbsolutePathInFileNameError(LoomengineUtilsError):
    pass

class WrongNumberOfFileNamesError(LoomengineUtilsError):
    pass

class NoFilesMatchError(LoomengineUtilsError):
    pass

class MultipleFilesMatchError(LoomengineUtilsError):
    pass

class ValidationError(LoomengineUtilsError):
    pass
