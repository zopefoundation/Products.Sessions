############################################################################
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
############################################################################
# BBB location for APIs now defined in Products.Sessions.interfaces

from .interfaces import BrowserIdManagerErr  # noqa: F401
from .interfaces import IBrowserIdManager
from .interfaces import ISessionDataManager
from .interfaces import SessionDataManagerErr  # noqa: F401


BrowserIdManagerInterface = IBrowserIdManager
SessionDataManagerInterface = ISessionDataManager
