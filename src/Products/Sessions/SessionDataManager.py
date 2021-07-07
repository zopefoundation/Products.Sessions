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
from AccessControl.Permissions import access_contents_information
from AccessControl.Permissions import view_management_screens
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
from .permissions import access_session_data
from .permissions import access_user_session_data
from .permissions import change_session_data_managers
from Products.Transience.Transience import TransientObjectContainer


bad_path_chars_in = re.compile(r'[^a-zA-Z0-9-_~\,\. \/]').search
LOG = getLogger('SessionDataManager')
# Default settings for the standard temporary session data container
default_sdc_settings = {
    'title': '',
    'timeout_mins': 20,
    'addNotification': '',
    'delNotification': '',
    'limit': 0,
    'period_secs': 20,
}


constructSessionDataManagerForm = DTMLFile(
    'dtml/addDataManager',
    globals()
)


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
    security.setPermissionDefault(change_session_data_managers, ['Manager'])
    security.setPermissionDefault(view_management_screens, ['Manager'])
    security.setPermissionDefault(
        access_contents_information,
        ['Manager', 'Anonymous'],
    )
    security.setPermissionDefault(access_user_session_data, ['Manager'])
    security.setPermissionDefault(
        access_session_data,
        ['Manager', 'Anonymous', ],
    )

    manage_sessiondatamgr = DTMLFile(
        'dtml/manageDataManager',
        globals()
    )

    # INTERFACE METHODS FOLLOW

    @security.protected(access_session_data)
    def getSessionData(self, create=1):
        """ """
        key = self.getBrowserIdManager().getBrowserId(create=create)
        if key is not None:
            return self._getSessionDataObject(key)

    @security.protected(access_session_data)
    def hasSessionData(self):
        """ """
        key = self.getBrowserIdManager().getBrowserId(create=0)
        if key is None:
            return 0
        return self._hasSessionDataObject(key)

    @security.protected(access_user_session_data)
    def getSessionDataByKey(self, key):
        return self._getSessionDataObjectByKey(key)

    @security.protected(access_contents_information)
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

    @security.protected(change_session_data_managers)
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

    @security.protected(change_session_data_managers)
    def setTitle(self, title):
        """ """
        if not title:
            self.title = ''
        else:
            self.title = str(title)

    @security.protected(change_session_data_managers)
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

    @security.protected(view_management_screens)
    def getContainerPath(self):
        """ """
        if self.obpath is not None:
            return '/'.join(self.obpath)
        return ''  # blank string represents undefined state

    @security.protected(view_management_screens)
    def hasSessionDataContainer(self):
        """ ZMI helper: do we have a valid session data container? """
        container = self._getSessionDataContainer()
        if container is not None and \
           getattr(container, 'new_or_existing', None) is not None:
            return True

    @security.protected(view_management_screens)
    def usesDefaultSessionDataContainer(self):
        """ ZMI helper: is the default temporary folder session container used?
        """
        return self.obpath == ['', 'temp_folder', 'session_data']

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
            # If this is a default configuration then the session data
            # container is inside a memory-based temporary folder, which
            # is wiped after each restart. Try to create it.
            if self.usesDefaultSessionDataContainer():
                try:
                    return self._setDefaultSessionDataContainer()
                except (AttributeError, KeyError):
                    # Temporary folder doesn't exist, give up
                    pass

            err = "External session data container '%s' not found."
            LOG.warning(err % '/'.join(self.obpath))
            return None

    def _setDefaultSessionDataContainer(self):
        tf = self.unrestrictedTraverse('/temp_folder')
        settings = self.getDefaultSessionDataContainerSettings()
        sdc = TransientObjectContainer('session_data', **settings)
        tf._setObject('session_data', sdc)
        LOG.info(u'Added session data container at /temp_folder/session_data')

        # Prevent accidental deletion by adding it to the reserved names
        tf_reserved = getattr(tf, '_reserved_names', ())
        if 'session_data' not in tf_reserved:
            tf._reserved_names = tf_reserved + ('session_data',)

        return self.unrestrictedTraverse(self.obpath)

    @security.protected(view_management_screens)
    def getDefaultSessionDataContainerSettings(self):
        """ ZMI helper: Return the session data container default settings """
        return getattr(self, '_sdc_settings', default_sdc_settings)

    @security.protected(change_session_data_managers)
    def manage_changeSDCDefaults(self,
                                 title='',
                                 timeout_mins=20,
                                 addNotification='',
                                 delNotification='',
                                 limit=0,
                                 period_secs=20,
                                 REQUEST=None):
        """ Collect settings for the default session data container """
        self._sdc_settings = {
            'title': title,
            'timeout_mins': timeout_mins,
            'addNotification': addNotification,
            'delNotification': delNotification,
            'limit': limit,
            'period_secs': period_secs,
        }

        if REQUEST is not None:
            msg = ('Session data container changes saved. They will be applied'
                   ' when you restart the Zope process.')
            return self.manage_sessiondatamgr(manage_tabs_message=msg)

    @security.protected(view_management_screens)
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
