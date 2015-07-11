from django.test import TestCase

class ImmutableModelsTestCase(TestCase):

    def roundTripJson(self, model):
        cls = model.__class__
        id1 = model._id
        model = cls.create(model.to_json())
        self.assertEqual(str(model._id), str(id1))

    def roundTripObj(self, model):
        cls = model.__class__
        id1 = model._id
        model = cls.create(model.to_obj())
        self.assertEqual(str(model._id), str(id1))
