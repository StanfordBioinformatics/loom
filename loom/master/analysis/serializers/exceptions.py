from rest_framework import serializers

class InvalidDataForCreateError(serializers.ValidationError):
    def __init__(self, Serializer, data):
        Exception.__init__(self, 'Could not create model %s from data %s' % (Serializer.Meta.model, data))


class InvalidDataForUpdateError(serializers.ValidationError):
    def __init__(self, instance, data):
        Exception.__init__(self, 'Could not update model %s with data %s' % (instance.__class__.__name__, data))


class UpdateNotAllowedError(Exception):
    def __init__(self, instance):
        Exception.__init__(self, 'Update not allowed on model %s' % instance.__class__.__name__)

class CreateNotAllowedError(Exception):
    def __init__(self, model):
        Exception.__init__(self, 'Create not supported on model %s. Use a related class.' % model.__name__)
