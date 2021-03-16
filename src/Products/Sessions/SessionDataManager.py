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

import re
import sys
from logging import getLogger

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import Implicit
from Acquisition import aq_inner
from Acquisition import aq_parent
from App.Management import Tabs
from App.special_dtml import DTMLFile
from OFS.owner import Owned
from OFS.role import RoleManager
from OFS.SimpleItem import Item
from Persistence import Persistent
from ZODB.POSException import ConflictError
from zope.interface import implementer
from ZPublisher.BeforeTraverse import registerBeforeTraverse
from ZPublisher.BeforeTraverse import unregisterBeforeTraverse

from .BrowserIdManager import BROWSERID_MANAGER_NAME
from .common import DEBUG
from .interfaces import ISessionDataManager
from .interfaces import SessionDataManagerErr
from .SessionPermissions import ACCESS_CONTENTS_PERM
from .SessionPermissions import ACCESS_SESSIONDATA_PERM
from .SessionPermissions import ARBITRARY_SESSIONDATA_PERM
from .SessionPermissions import CHANGE_DATAMGR_PERM
from .SessionPermissions import MGMT_SCREEN_PERM


bad_path_chars_in = re.compile(r'[^a-zA-Z0-9-_~\,\. \/]').search
LOG = getLogger('SessionDataManager')

constructSessionDataManagerForm = DTMLFile(
    'dtml/addDataManager',
    globals()
)

ADD_SESSION_DATAMANAGER_PERM = "Add Session Data Manager"


def constructSessionDataManager(
    self,
    id,
    title='',
    path=None,
    requestName=None,
    REQUEST=None
):
    """ """
    ob = SessionDataManager(id, path, title, requestName)
    self._setObject(id, ob)
    if REQUEST is not None:
        return self.manage_main(self, REQUEST, update_menu=1)


class SessionIdManagerErr(Exception):
    pass


@implementer(ISessionDataManager)
class SessionDataManager(Item, Implicit, Persistent, RoleManager, Owned, Tabs):
    """The Zope default session data manager implementation."""

    meta_type = 'Session Data Manager'
    zmi_icon = 'far fa-clock'

    manage_options = (
        {
            'label': 'Settings',
            'action': 'manage_sessiondatamgr',
        },
        {
            'label': 'Security',
            'action': 'manage_access',
        },
        {
            'label': 'Ownership',
            'action': 'manage_owner',
        },
    )

    security = ClassSecurityInfo()
    security.declareObjectPublic()

    ok = {
        'meta_type': 1,
        'id': 1,
        'title': 1,
        'zmi_icon': 1,
        'title_or_id': 1,
    }
    security.setDefaultAccess(ok)
    security.setPermissionDefault(CHANGE_DATAMGR_PERM, ['Manager'])
    security.setPermissionDefault(MGMT_SCREEN_PERM, ['Manager'])
    security.setPermissionDefault(
        ACCESS_CONTENTS_PERM,
        ['Manager', 'Anonymous'],
    )
    security.setPermissionDefault(ARBITRARY_SESSIONDATA_PERM, ['Manager'])
    security.setPermissionDefault(
        ACCESS_SESSIONDATA_PERM,
        ['Manager', 'Anonymous', ],
    )

    manage_sessiondatamgr = DTMLFile(
        'dtml/manageDataManager',
        globals()
    )

    # INTERFACE METHODS FOLLOW

    @security.protected(ACCESS_SESSIONDATA_PERM)
    def getSessionData(self, create=1):
        """ """
        key = self.getBrowserIdManager().getBrowserId(create=create)
        if key is not None:
            return self._getSessionDataObject(key)

    @security.protected(ACCESS_SESSIONDATA_PERM)
    def hasSessionData(self):
        """ """
        key = self.getBrowserIdManager().getBrowserId(create=0)
        if key is None:
            return 0
        return self._hasSessionDataObject(key)

    @security.protected(ARBITRARY_SESSIONDATA_PERM)
    def getSessionDataByKey(self, key):
        return self._getSessionDataObjectByKey(key)

    @security.protected(ACCESS_CONTENTS_PERM)
    def getBrowserIdManager(self):
        """ """
        mgr = getattr(self, BROWSERID_MANAGER_NAME, None)
        if mgr is None:
            raise SessionDataManagerErr(
                'No browser id manager named %s could be found.' %
                BROWSERID_MANAGER_NAME
            )
        return mgr

    # END INTERFACE METHODS

    def __init__(self, id, path=None, title='', requestName=None):
        self.id = id
        self.setContainerPath(path)
        self.setTitle(title)
        self._requestSessionName = requestName

    @security.protected(CHANGE_DATAMGR_PERM)
    def manage_changeSDM(
        self,
        title,
        path=None,
        requestName=None,
        REQUEST=None
    ):
        """ """
        self.setContainerPath(path)
        self.setTitle(title)
        if requestName:
            if requestName != self._requestSessionName:
                self.updateTraversalData(requestName)
        else:
            self.updateTraversalData(None)
        if REQUEST is not None:
            return self.manage_sessiondatamgr(
                self,
                REQUEST,
                manage_tabs_message='Changes saved.'
            )

    @security.protected(CHANGE_DATAMGR_PERM)
    def setTitle(self, title):
        """ """
        if not title:
            self.title = ''
        else:
            self.title = str(title)

    @security.protected(CHANGE_DATAMGR_PERM)
    def setContainerPath(self, path=None):
        """ """
        if not path:
            self.obpath = None  # undefined state
        elif isinstance(path, str):
            if bad_path_chars_in(path):
                raise SessionDataManagerErr(
                    'Container path contains characters invalid in a Zope '
                    'object path'
                )
            self.obpath = path.split('/')
        elif isinstance(path, (list, tuple)):
            self.obpath = list(path)  # sequence
        else:
            raise SessionDataManagerErr('Bad path value %s' % path)

    @security.protected(MGMT_SCREEN_PERM)
    def getContainerPath(self):
        """ """
        if self.obpath is not None:
            return '/'.join(self.obpath)
        return ''  # blank string represents undefined state

    @security.protected(MGMT_SCREEN_PERM)
    def hasSessionDataContainer(self):
        """ ZMI helper: do we have a valid session data container? """
        container = self._getSessionDataContainer()
        if container is not None and \
           getattr(container, 'new_or_existing', None) is not None:
            return True

    def _hasSessionDataObject(self, key):
        """ """
        c = self._getSessionDataContainer()
        return key in c

    def _getSessionDataObject(self, key):
        """ returns new or existing session data object """
        container = self._getSessionDataContainer()
        if container is None:
            return None

        ob = container.new_or_existing(key)
        # hasattr hides conflicts; be explicit by comparing to None
        # because otherwise __len__ of the requested object might be called!
        if getattr(ob, '__of__', None) is not None and \
           getattr(ob, 'aq_parent', None) is not None:
            # splice ourselves into the acquisition chain
            return ob.__of__(self.__of__(ob.aq_parent))
        return ob.__of__(self)

    def _getSessionDataObjectByKey(self, key):
        """ returns new or existing session data object """
        container = self._getSessionDataContainer()
        if container is None:
            return None

        ob = container.get(key)
        if ob is not None:
            # hasattr hides conflicts; be explicit by comparing to None
            # because otherwise __len__ of the requested object might be
            # called!
            if getattr(ob, '__of__', None) is not None and \
               getattr(ob, 'aq_parent', None) is not None:
                # splice ourselves into the acquisition chain
                return ob.__of__(self.__of__(ob.aq_parent))
            return ob.__of__(self)

    def _getSessionDataContainer(self):
        """ Do not cache the results of this call.  Doing so breaks the
        transactions for mounted storages. """
        if self.obpath is None:
            err = 'Session data container is unspecified in %s' % self.getId()
            LOG.warning(err)
            return None

        try:
            # This should arguably use restrictedTraverse, but it
            # currently fails for mounted storages.  This might
            # be construed as a security hole, albeit a minor one.
            # unrestrictedTraverse is also much faster.
            # hasattr hides conflicts
            if DEBUG and not getattr(self, '_v_wrote_dc_type', None):
                args = '/'.join(self.obpath)
                LOG.debug('External data container at %s in use' % args)
                self._v_wrote_dc_type = 1
            return self.unrestrictedTraverse(self.obpath)
        except ConflictError:
            raise
        except Exception:
            err = "External session data container '%s' not found."
            LOG.warning(err % '/'.join(self.obpath))
            return None

    @security.protected(MGMT_SCREEN_PERM)
    def getRequestName(self):
        """ """
        return self._requestSessionName or ''

    def manage_afterAdd(self, item, container):
        """ Add our traversal hook """
        self.updateTraversalData(self._requestSessionName)

    def manage_beforeDelete(self, item, container):
        """ Clean up on delete """
        self.updateTraversalData(None)

    def updateTraversalData(self, requestSessionName=None):
        # Note this cant be called directly at add -- manage_afterAdd will
        # work though.
        parent = aq_parent(aq_inner(self))

        if getattr(self, '_hasTraversalHook', None):
            unregisterBeforeTraverse(parent, 'SessionDataManager')
            del self._hasTraversalHook
            self._requestSessionName = None

        if requestSessionName:
            hook = SessionDataManagerTraverser(requestSessionName, self.id)
            registerBeforeTraverse(parent, hook, 'SessionDataManager', 50)
            self._hasTraversalHook = 1
            self._requestSessionName = requestSessionName


InitializeClass(SessionDataManager)


class SessionDataManagerTraverser(Persistent):

    def __init__(self, requestSessionName, sessionDataManagerName):
        self._requestSessionName = requestSessionName
        self._sessionDataManager = sessionDataManagerName

    def __call__(self, container, request):
        """
        This method places a session data object reference in
        the request.  It is called on each and every request to Zope in
        Zopes after 2.5.0 when there is a session data manager installed
        in the root.
        """
        try:
            sdmName = self._sessionDataManager
            if not isinstance(sdmName, str):
                # Zopes v2.5.0 - 2.5.1b1 stuck the actual session data
                # manager object in _sessionDataManager in order to use
                # its getSessionData method.  We don't actually want to
                # do this, because it's safer to use getattr to get the
                # data manager object by name.  Using getattr also puts
                # the sdm in the right context automatically.  Here we
                # pay the penance for backwards compatibility:
                sdmName = sdmName.id
            sdm = getattr(container, sdmName)
            getSessionData = sdm.getSessionData
        except Exception:
            msg = 'Session automatic traversal failed to get session data'
            LOG.warning(msg, exc_info=sys.exc_info())
            return

        # set the getSessionData method in the "lazy" namespace
        if self._requestSessionName is not None:
            request.set_lazy(self._requestSessionName, getSessionData)
