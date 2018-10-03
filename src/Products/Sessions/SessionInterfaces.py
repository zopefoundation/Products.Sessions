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

# flake8: NOQA: E401

# This is a file to define public API in the base namespace of the package.
# use: isort:skip to supress all isort related warnings / errors,
# as this file should be logically grouped imports

from Products.Sessions.interfaces import BrowserIdManagerErr
from Products.Sessions.interfaces import IBrowserIdManager
from Products.Sessions.interfaces import ISessionDataManager
from Products.Sessions.interfaces import SessionDataManagerErr


BrowserIdManagerInterface = IBrowserIdManager
SessionDataManagerInterface = ISessionDataManager
