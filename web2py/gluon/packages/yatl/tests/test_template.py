#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Unit tests for gluon.template
"""

import unittest
import sys

from yatl import render
from yatl.template import DummyResponse, RestrictedError, NOESCAPE


class TestTemplate(unittest.TestCase):

    def testRun(self):
        self.assertEqual(render(content='{{for i in range(n):}}{{=i}}{{pass}}',
                                context=dict(n=3)), '012')
        self.assertEqual(render(content='{{if n>2:}}ok{{pass}}',
                                context=dict(n=3)), 'ok')
        self.assertEqual(
            render(content='{{try:}}{{n/0}}{{except:}}fail{{pass}}',
                   context=dict(n=3)), 'fail')
        self.assertEqual(render(content='{{="<&>"}}'), '&lt;&amp;&gt;')
        self.assertEqual(render(content='"abc"'), '"abc"')
        self.assertEqual(render(content='"a\'bc"'), '"a\'bc"')
        self.assertEqual(render(content='"a\"bc"'), '"a\"bc"')
        self.assertEqual(render(content=r'"a\"bc"'), r'"a\"bc"')
        self.assertEqual(render(content=r'"""abc\""""'), r'"""abc\""""')

    def testEqualWrite(self):
        "test generation of response.write"
        self.assertEqual(render(content='{{=2+2}}'), '4')
        self.assertEqual(render(content='{{="abc"}}'), 'abc')
        # whitespace is stripped
        self.assertEqual(render(content='{{ ="abc"}}'), 'abc')
        self.assertEqual(render(content='{{ ="abc" }}'), 'abc')
        self.assertEqual(render(content='{{pass\n="abc" }}'), 'abc')
        # = recognized only at the beginning of a physical line
        self.assertEqual(render(
            content='{{xyz = "xyz"\n="abc"\n="def"\n=xyz }}'), 'abcdefxyz')
        # = in python blocks
        self.assertEqual(render(content='{{if True:\n="abc"\npass }}'), 'abc')
        self.assertEqual(
            render(content='{{if True:\n="abc"\npass\n="def" }}'), 'abcdef')
        self.assertEqual(
            render(content='{{if False:\n="abc"\npass\n="def" }}'), 'def')
        self.assertEqual(render(
            content='{{if True:\n="abc"\nelse:\n="def"\npass }}'), 'abc')
        self.assertEqual(render(
            content='{{if False:\n="abc"\nelse:\n="def"\npass }}'), 'def')
        # codeblock-leading = handles internal newlines, escaped or not
        self.assertEqual(render(content='{{=list((1,2,3))}}'), '[1, 2, 3]')
        self.assertEqual(render(content='{{=list((1,2,\\\n3))}}'), '[1, 2, 3]')
        self.assertEqual(render(content='{{=list((1,2,\n3))}}'), '[1, 2, 3]')
        # ...but that means no more = operators in the codeblock
        self.assertRaises(SyntaxError, render, content='{{="abc"\n="def" }}')
        # = embedded in codeblock won't handle newlines in its argument
        self.assertEqual(
            render(content='{{pass\n=list((1,2,\\\n3))}}'), '[1, 2, 3]')
        self.assertRaises(
            SyntaxError, render, content='{{pass\n=list((1,2,\n3))}}')

    def testWithDummyFileSystem(self):
        from os.path import join as pjoin
        import contextlib
        if sys.version_info[0] == 2:
            from cStringIO import StringIO
        else:
            from io import StringIO

        @contextlib.contextmanager
        def monkey_patch(module, fn_name, patch):
            try:
                unpatch = getattr(module, fn_name)
            except AttributeError:
                unpatch = None
            setattr(module, fn_name, patch)
            try:
                yield
            finally:
                if unpatch is None:
                    delattr(module, fn_name)
                else:
                    setattr(module, fn_name, unpatch)

        def dummy_open(path):
            if path == pjoin('views', 'layout.html'):
                return ("{{block left_sidebar}}left{{end}}"
                        "{{include}}" 
                        "{{block right_sidebar}}right{{end}}")
            elif path == pjoin('views', 'layoutbrackets.html'):
                return ("[[block left_sidebar]]left[[end]]"
                        "[[include]]"
                        "[[block right_sidebar]]right[[end]]")
            elif path == pjoin('views', 'default', 'index.html'):
                return ("{{extend 'layout.html'}}"
                        "{{block left_sidebar}}{{super}} {{end}}"
                        "to"
                        "{{block right_sidebar}} {{super}}{{end}}")
            elif path == pjoin('views', 'default', 'indexbrackets.html'):
                return ("[[extend 'layoutbrackets.html']]"
                        "[[block left_sidebar]][[super]] [[end]]"
                        "to"
                        "[[block right_sidebar]] [[super]][[end]]")
            elif path == pjoin('views', 'default', 'missing.html'):
                return ("{{extend 'wut'}}"
                        "{{block left_sidebar}}{{super}} {{end}}"
                        "to"
                        "{{block right_sidebar}} {{super}}{{end}}")
            elif path == pjoin('views', 'default', 'noescape.html'):
                return "{{=NOESCAPE('<script></script>')}}"
            raise IOError
        
        self.assertEqual(
            render(filename=pjoin('views', 'default', 'index.html'),
                   path='views', reader=dummy_open),
            'left to right')
        self.assertEqual(
            render(filename=pjoin('views', 'default', 'indexbrackets.html'),
                   path='views', delimiters='[[ ]]', reader=dummy_open),
            'left to right')
        #self.assertRaises(
        #    RestrictedError,
        #    render,
        #    filename=pjoin('views', 'default', 'missing.html'),
        #    path='views',
        #    reader=dummy_open)
        response = DummyResponse()
        response.delimiters = ('[[', ']]')
        self.assertEqual(
            render(filename=pjoin('views', 'default', 'indexbrackets.html'),
                   path='views', context={'response': response}, reader=dummy_open),
            'left to right')
        self.assertEqual(
            render(filename=pjoin('views', 'default', 'noescape.html'),
                   context={'NOESCAPE': NOESCAPE}, reader=dummy_open),
            '<script></script>')
