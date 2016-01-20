class Error(Exception):
    pass

class ConvertToJsonError(Error):
    pass

class InvalidJsonError(Error):
    pass

class ConvertToDictError(Error):
    pass

class MissingValidationSchemaError(Error):
    pass

class ModelValidationError(Error):
    pass

class InvalidValidationSchemaError(Error):
    pass

class ModelNotFoundError(Error):
    pass

class UpdateIdMismatchError(Error):
    pass

class NoSaveAllowedError(Error):
    pass

class AttributeDoesNotExist(Error):
    pass

class MutableChildError(Error):
    pass

class CouldNotFindSubclassError(Error):
    pass

class CouldNotFindUniqueSubclassError(Error):
    pass

class ForeignKeyInChildError(Error):
    pass

class ImmutableChildWithForeignKeyError(Error):
    pass

class AttemptedToUpdateImmutableError(Error):
    pass

class UniqueIdMismatchError(Error):
    pass

class ParentNestedInChildError(Error):
    pass
