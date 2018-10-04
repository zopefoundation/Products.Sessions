##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

from . import fauxtime
from Products.Transience.Transience import TransientObjectContainer
from unittest import makeSuite
from unittest import TestCase
from unittest import TestSuite

import Products.Transience.Transience
import Products.Transience.TransientObject
import six
import time as oldtime


class TestTransientObject(TestCase):

    def setUp(self):
        Products.Transience.Transience.time = fauxtime
        Products.Transience.TransientObject.time = fauxtime
        Products.Transience.Transience.setStrict(1)
        self.errmargin = .20
        self.timeout = fauxtime.timeout
        self.t = TransientObjectContainer(
            'sdc', timeout_mins=self.timeout // 60)

    def tearDown(self):
        Products.Transience.Transience.time = oldtime
        Products.Transience.TransientObject.time = oldtime
        Products.Transience.Transience.setStrict(0)
        self.t = None
        del self.t

    def test_id(self):
        t = self.t.new('xyzzy')
        self.assertNotEqual(t.getId(), 'xyzzy')  # dont acquire
        self.assertEqual(t.getContainerKey(), 'xyzzy')

    def test_validate(self):
        t = self.t.new('xyzzy')
        self.assertTrue(t.isValid())
        t.invalidate()
        self.assertFalse(t.isValid())

    def test_getLastAccessed(self):
        t = self.t.new('xyzzy')
        ft = fauxtime.time()
        self.assertLessEqual(t.getLastAccessed(), ft)

    def test_getCreated(self):
        t = self.t.new('xyzzy')
        ft = fauxtime.time()
        self.assertLessEqual(t.getCreated(), ft)

    def test_getLastModifiedUnset(self):
        t = self.t.new('xyzzy')
        self.assertIsNone(t.getLastModified())

    def test_getLastModifiedSet(self):
        t = self.t.new('xyzzy')
        t['a'] = 1
        self.assertIsNotNone(t.getLastModified())

    def testSetLastModified(self):
        t = self.t.new('xyzzy')
        t.setLastModified()
        self.assertIsNotNone(t.getLastModified())

    def test_setLastAccessed(self):
        t = self.t.new('xyzzy')
        ft = fauxtime.time()
        self.assertLessEqual(t.getLastAccessed(), ft)
        fauxtime.sleep(self.timeout * 2)   # go to sleep past the granularity
        ft2 = fauxtime.time()
        t.setLastAccessed()
        ft3 = fauxtime.time()
        self.assertLessEqual(t.getLastAccessed(), ft3)
        self.assertGreaterEqual(t.getLastAccessed(), ft2)

    def _genKeyError(self, t):
        return t.get('foobie')

    def _genLenError(self, t):
        return t.len()

    def test_dictionaryLike(self):
        t = self.t.new('keytest')
        t.update(data)
        if six.PY2:
            assertCountEqual = self.assertItemsEqual
        else:
            assertCountEqual = self.assertCountEqual
        assertCountEqual(t.keys(), data.keys())
        assertCountEqual(t.values(), data.values())
        assertCountEqual(t.items(), data.items())
        for k in data.keys():
            self.assertEqual(t.get(k), data.get(k))
        self.assertIsNone(t.get('foobie'))
        with self.assertRaises(AttributeError):
            self._genLenError(t)
        self.assertIsNone(t.get('foobie', None))
        # Test with .has_key() are necessary:
        # as t did not have a __contains__ method
        # normally you would test like that:
        # >>> self.assertTrue('a' in t)
        # >>> self.assertFalse('foobie' in t)
        self.assertTrue(t.has_key('a'))  # NOQA: W601
        self.assertFalse(t.has_key('foobie'))  # NOQA: W601
        t.clear()
        self.assertEqual(len(t.keys()), 0)

    def test_TTWDictionary(self):
        t = self.t.new('mouthfultest')
        t.set('foo', 'bar')
        self.assertEqual(t['foo'], 'bar')
        self.assertEqual(t.get('foo'), 'bar')
        t.set('foobie', 'blech')
        t.delete('foobie')
        self.assertEqual(t.get('foobie'), None)

    def test_repr_leaking_information(self):
        # __repr__ used to show all contents, which could lead to sensitive
        # information being visible in e.g. the ErrorLog object.
        t = self.t.new('password-storing-session')
        t.set('__ac_password__', 'secret')
        self.assertNotIn('secret', repr(t), '__repr__ leaks: %s' % repr(t))


def test_suite():
    testsuite = makeSuite(TestTransientObject, 'test')
    alltests = TestSuite((testsuite, ))
    return alltests


data = {
    'a': 'a',
    1: 1,
    'Mary': 'no little lamb for you today!',
    'epoch': 999999999,
    'fauxtime': fauxtime,
}
