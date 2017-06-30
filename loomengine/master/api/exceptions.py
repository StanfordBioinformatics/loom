class Error(Exception):
    pass

class ConcurrentModificationError(Exception):
    """Raised by the "save" method when the model has
    been changed in the database since it was loaded.
    """
    pass


class SaveRetriesExceededError(Exception):
    """Raised by the "save" method when saving raises
    a ConcurrentModificationError after the allowed
    number of retries is exhausted.
    """
    pass
