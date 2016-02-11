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

class WrongRenameLengthError(Error):
    pass
