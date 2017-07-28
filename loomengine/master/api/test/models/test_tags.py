from django.test import TestCase

from api.test.models.test_templates import get_workflow
from api.models.tags import *


class TestTag(TestCase):

    def testCreate(self):
        template = get_workflow()
        tag = Tag(
            name='tag1',
            type='template',
            template=template)
        tag.full_clean()
        tag.save()
        self.assertTrue(tag.id)
