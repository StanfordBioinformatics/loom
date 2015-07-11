from .dummy import DummyResourceManager

def get_resource_manager():
    return DummyResourceManager

ResourceManager = get_resource_manager()
