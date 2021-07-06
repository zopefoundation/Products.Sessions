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
Transience initialization routines
"""

# flake8: NOQA: E401

# This is a file to define public API in the base namespace of the package.
# use: isort:skip to supress all isort related warnings / errors,
# as this file should be logically grouped imports

import ZODB  # this is to help out testrunner, don't remove.

from . import Transience
from .permissions import add_transient_containers
# import of MaxTransientObjectsExceeded for easy import from scripts,
# this is protected by a module security info declaration in the
# Sessions package.
from .Transience import MaxTransientObjectsExceeded


def initialize(context):
    context.registerClass(
        Transience.TransientObjectContainer,
        permission=add_transient_containers,
        constructors=(Transience.constructTransientObjectContainerForm,
                      Transience.constructTransientObjectContainer)
        )
