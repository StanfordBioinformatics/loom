class ModelTestMixin(object):

    def roundTrip(self, model):
        cls = model.__class__
        id1 = model._id
        
        model1 = cls.create(model.to_json())
        self.assertEqual(str(model._id), str(id1))
        
        model2 = cls.create(model.to_struct())
        self.assertEqual(str(model._id), str(id1))
