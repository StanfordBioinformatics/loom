class Error(Exception):
    pass

class ConcurrentModificationError(Exception):
    pass

class SaveRetriesExceededError(Exception):
    pass

class NoTemplateInputMatchError(Exception):
    pass

class ChannelNameCollisionError(Exception):
    pass

