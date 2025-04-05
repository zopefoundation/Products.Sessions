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

from zope.deferredimport import deprecated


deprecated(
    "All interfaces for Products.Sessions have moved to"
    " Products.Sessions.interfaces. Please import from there."
    " This backward compatibility shim will be removed in"
    " Products.Sessions version 7.",
    BrowserIdManagerErr='Products.Sessions.interfaces:BrowserIdManagerErr',
    IBrowserIdManager='Products.Sessions.interfaces:IBrowserIdManager',
    ISessionDataManager='Products.Sessions.interfaces:ISessionDataManager',
    SessionDataManagerErr='Products.Sessions.interfaces:SessionDataManagerErr',
    BrowserIdManagerInterface='Products.Sessions.interfaces:IBrowserIdManager',
    SessionDataManagerInterface=(
        'Products.Sessions.interfaces:ISessionDataManager'),)
