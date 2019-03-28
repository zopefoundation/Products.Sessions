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
"""
Module used for testing transience (BTree-API-conforming data structure)
"""

import sys

from Persistence.mapping import PersistentMapping


class FakeIOBTree(PersistentMapping):

    def keys(self, min, max):
        List = []
        if min is None:
            min = 0

        if max is None:
            max = sys.maxsize

        for k in self.data:
            if min <= k <= max:
                List.append(k)
        return List
