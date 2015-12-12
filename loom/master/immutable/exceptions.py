class ConvertToJsonError(Exception):
    pass

class InvalidJsonError(Exception):
    pass

class ConvertToDictError(Exception):
    pass

class MissingValidationSchemaError(Exception):
    pass

class ModelValidationError(Exception):
    pass

class InvalidValidationSchemaError(Exception):
    pass

class ModelNotFoundError(Exception):
    pass

class UpdateIdMismatchError(Exception):
    pass

class NoSaveAllowedError(Exception):
    pass

class AttributeDoesNotExist(Exception):
    pass

class MutableChildError(Exception):
    pass

class CouldNotFindSubclassError(Exception):
    pass

class CouldNotFindUniqueSubclassError(Exception):
    pass

class ForeignKeyInChildError(Exception):
    pass

class ImmutableChildWithForeignKeyException(Exception):
    pass

class AttemptedToUpdateImmutableError(Exception):
    pass

class UniqueIdMismatchError(Exception):
    pass

class ParentNestedInChildException(Exception):
    pass
