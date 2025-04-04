##########################################################################
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
##########################################################################
# BBB location for interfaces now defined in Products.Transience.interfaces

from zope.deferredimport import deprecated


deprecated(
    "All interfaces for Products.Transience have moved to"
    " Products.Transience.interfaces. Please import from there."
    " This backward compatibility shim will be removed in"
    " Products.Sessions version 7.",
    Transient='Products.Transience.interfaces:ITransient',
    DictionaryLike='Products.Transience.interfaces:IDictionaryLike',
    ItemWithId='Products.Transience.interfaces:IItemWithId',
    TTWDictionary='Products.Transience.interfaces:ITTWDictionary',
    ImmutablyValuedMappingOfPickleableObjects=(
        'Products.Transience.interfaces:'
        'IImmutablyValuedMappingOfPickleableObjects'),
    HomogeneousItemContainer=(
        'Products.Transience.interfaces:IHomogeneousItemContainer'),
    StringKeyedHomogeneousItemContainer=(
        'Products.Transience.interfaces:IStringKeyedHomogeneousItemContainer'),
    TransientItemContainer=(
        'Products.Transience.interfaces:ITransientItemContainer'),
)
