from django.test import TestCase

class ImmutableModelsTestCase(TestCase):

    def roundTripJson(self, model):
        cls = model.__class__
        id1 = model._id
        model = cls.create(model.to_json())
        self.assertEqual(str(model._id), str(id1))

    def roundTripStruct(self, model):
        cls = model.__class__
        id1 = model._id
        model = cls.create(model.to_struct())
        self.assertEqual(str(model._id), str(id1))
