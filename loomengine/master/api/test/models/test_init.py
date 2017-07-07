from django.test import TestCase

from api.models import render_from_template, render_string_or_list, ArrayInputContext


class TestRenderFromTemplate(TestCase):

    def testRenderFromTemplate(self):
        raw_text = 'My name is {{name}}'
        context = {'name': 'Inigo'}
        rendered_text = render_from_template(raw_text, context)
        self.assertEqual(rendered_text, 'My name is Inigo')

class TestRenderFromStringOrList(TestCase):

    def testString(self):
        raw_text = 'Name: {{ name }}'
        context = {'name': 'Inigo'}
        rendered_text = render_string_or_list(raw_text, context)
        self.assertEqual(rendered_text, 'Name: Inigo')

    def testList(self):
        raw_text = ['Name: {{ name }}', 'Nome: {{ name }}', 'Nombre: {{ name }}',]
        context = {'name': 'Inigo'}
        rendered_text = render_string_or_list(raw_text, context)
        self.assertEqual(rendered_text, ['Name: Inigo', 'Nome: Inigo', 'Nombre: Inigo'])

class TestArrayInputContext(TestCase):

    filenames = ['one', 'two.txt', 'three', 'two.txt', 'three', 'three']
    integers = [1, 2, 3, 2, 3, 3]

    def testIterFilenames(self):
        context = ArrayInputContext(self.filenames, 'file')
        filenames = [item for item in context]
        self.assertEqual(
            filenames,
            ['one', 'two__0__.txt', 'three__0__', 'two__1__.txt',
             'three__1__', 'three__2__']
        )

    def testGetitemFilenames(self):
        context = ArrayInputContext(self.filenames, 'file')
        self.assertEqual(context[1], 'two__0__.txt')

    def testStrFilenames(self):
        context = ArrayInputContext(self.filenames, 'file')
        string = str(context)
        self.assertEqual(
            string,
            'one two__0__.txt three__0__ two__1__.txt three__1__ three__2__'
        )
 
    def testIterIntegers(self):
        context = ArrayInputContext(self.integers, 'integer')
        values = [item for item in context]
        self.assertEqual(
            values,
            self.integers)


    def testGetitemIntegers(self):
        context = ArrayInputContext(self.integers, 'integer')
        values = [item for item in context]
        self.assertEqual(context[1], 2)

    def testStrIntegers(self):
        context = ArrayInputContext(self.integers, 'integer')
        string = str(context)
        self.assertEqual(
            string,
            '1 2 3 2 3 3'
        )
