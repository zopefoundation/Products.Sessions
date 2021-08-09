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


import binascii
import logging
import os
# Use the system PRNG if possible
import random
import re
import sys
import time
from hashlib import sha256

import six
from six.moves.urllib.parse import quote
from six.moves.urllib.parse import urlparse
from six.moves.urllib.parse import urlunparse

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
from persistent import TimeStamp
from zope.interface import implementer
from ZPublisher.BeforeTraverse import queryBeforeTraverse
from ZPublisher.BeforeTraverse import registerBeforeTraverse
from ZPublisher.BeforeTraverse import unregisterBeforeTraverse

from .interfaces import BrowserIdManagerErr
from .interfaces import IBrowserIdManager
from .permissions import change_browser_id_managers


try:
    from html import escape
except ImportError:  # Python 2
    from cgi import escape


badidnamecharsin = re.compile(r'[\?&;,<> ]').search
badcookiecharsin = re.compile(r'[;,<>& ]').search
twodotsin = re.compile(r'(\w*\.){2,}').search

_marker = []

constructBrowserIdManagerForm = DTMLFile('dtml/addIdManager', globals())

BROWSERID_MANAGER_NAME = 'browser_id_manager'  # imported by SessionDataManager
ALLOWED_BID_NAMESPACES = ('form', 'cookies', 'url')
TRAVERSAL_APPHANDLE = 'BrowserIdManager'

LOG = logging.getLogger('Zope.BrowserIdManager')


try:
    random = random.SystemRandom()
    using_sysrandom = True
except NotImplementedError:
    using_sysrandom = False


def _randint(start, end):
    if not using_sysrandom:
        # This is ugly, and a hack, but it makes things better than
        # the alternative of predictability. This re-seeds the PRNG
        # using a value that is hard for an attacker to predict, every
        # time a random string is required. This may change the
        # properties of the chosen random sequence slightly, but this
        # is better than absolute predictability.
        random.seed(sha256(
            "%s%s%s" % (random.getstate(), time.time(), os.getpid())
        ).digest())
    return random.randint(start, end)


def constructBrowserIdManager(
    self,
    id=BROWSERID_MANAGER_NAME,
    title='',
    idname='_ZopeId',
    location=('cookies', 'form'),
    cookiepath='/',
    cookiedomain='',
    cookielifedays=0,
    cookiesecure=0,
    cookiehttponly=0,
    auto_url_encoding=0,
    REQUEST=None
):
    """ """
    ob = BrowserIdManager(id, title, idname, location, cookiepath,
                          cookiedomain, cookielifedays, cookiesecure,
                          cookiehttponly, auto_url_encoding)
    self._setObject(id, ob)
    ob = self._getOb(id)
    if REQUEST is not None:
        return self.manage_main(self, REQUEST, update_menu=1)


@implementer(IBrowserIdManager)
class BrowserIdManager(Item, Persistent, Implicit, RoleManager, Owned, Tabs):
    """ browser id management class
    """
    meta_type = 'Browser Id Manager'
    zmi_icon = 'far fa-id-card'

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
    security.setPermissionDefault(view_management_screens, ['Manager'])
    security.setPermissionDefault(
        access_contents_information,
        ['Manager', 'Anonymous'],
    )
    security.setPermissionDefault(change_browser_id_managers, ['Manager'])

    # BBB
    auto_url_encoding = 0
    cookie_http_only = 0

    def __init__(
        self,
        id,
        title='',
        idname='_ZopeId',
        location=('cookies', 'form'),
        cookiepath=('/'),
        cookiedomain='',
        cookielifedays=0,
        cookiesecure=0,
        cookiehttponly=0,
        auto_url_encoding=0
    ):
        self.id = str(id)
        self.title = str(title)
        self.setBrowserIdName(idname)
        self.setBrowserIdNamespaces(location)
        self.setCookiePath(cookiepath)
        self.setCookieDomain(cookiedomain)
        self.setCookieLifeDays(cookielifedays)
        self.setCookieSecure(cookiesecure)
        self.setCookieHTTPOnly(cookiehttponly)
        self.setAutoUrlEncoding(auto_url_encoding)

    # IBrowserIdManager
    @security.protected(access_contents_information)
    def hasBrowserId(self):
        """ See IBrowserIdManager.
        """
        try:
            return self.getBrowserId(create=0) is not None
        except BrowserIdManagerErr:
            return False

    @security.protected(access_contents_information)
    def getBrowserId(self, create=1):
        """ See IBrowserIdManager.
        """
        REQUEST = self.REQUEST
        # let's see if bid has already been attached to request
        bid = getattr(REQUEST, 'browser_id_', None)
        if bid is not None:
            # it's already set in this request so we can just return it
            # if it's well-formed
            if not isAWellFormedBrowserId(bid):
                # somebody screwed with the REQUEST instance during
                # this request.
                raise BrowserIdManagerErr(
                    'Ill-formed browserid in REQUEST.browser_id_:  %s' %
                    escape(bid)
                )
            return bid
        # fall through & ck form/cookie namespaces if bid is not in request.
        tk = self.browserid_name
        ns = self.browserid_namespaces
        for name in ns:
            if name == 'url':
                continue  # browser ids in url are checked by Traverser class
            current_ns = getattr(REQUEST, name, None)
            if current_ns is None:
                continue
            bid = current_ns.get(tk, None)
            if bid is not None:
                # hey, we got a browser id!
                if isAWellFormedBrowserId(bid):
                    # bid is not "plain old broken"
                    REQUEST.browser_id_ = bid
                    REQUEST.browser_id_ns_ = name
                    return bid
        # fall through if bid is invalid or not in namespaces
        if create:
            # create a brand new bid
            bid = getNewBrowserId()
            if 'cookies' in ns:
                self._setCookie(bid, REQUEST)
            REQUEST.browser_id_ = bid
            REQUEST.browser_id_ns_ = None
            return bid
        # implies a return of None if:
        # (not create=1) and (invalid or ((not in req) and (not in ns)))

    @security.protected(access_contents_information)
    def getBrowserIdName(self):
        """ See IBrowserIdManager.
        """
        return self.browserid_name

    @security.protected(access_contents_information)
    def isBrowserIdNew(self):
        """ See IBrowserIdManager.
        """
        if not self.getBrowserId(create=False):
            raise BrowserIdManagerErr('There is no current browser id.')
        # ns will be None if new
        return getattr(self.REQUEST, 'browser_id_ns_', None) is None

    @security.protected(access_contents_information)
    def isBrowserIdFromCookie(self):
        """ See IBrowserIdManager.
        """
        if not self.getBrowserId(create=False):
            raise BrowserIdManagerErr('There is no current browser id.')
        if getattr(self.REQUEST, 'browser_id_ns_') == 'cookies':
            return 1

    @security.protected(access_contents_information)
    def isBrowserIdFromForm(self):
        """ See IBrowserIdManager.
        """
        if not self.getBrowserId(create=False):
            raise BrowserIdManagerErr('There is no current browser id.')
        if getattr(self.REQUEST, 'browser_id_ns_') == 'form':
            return 1

    @security.protected(access_contents_information)
    def isBrowserIdFromUrl(self):
        """ See IBrowserIdManager.
        """
        if not self.getBrowserId(create=False):
            raise BrowserIdManagerErr('There is no current browser id.')
        if getattr(self.REQUEST, 'browser_id_ns_') == 'url':
            return 1

    @security.protected(access_contents_information)
    def flushBrowserIdCookie(self):
        """ See IBrowserIdManager.
        """
        if 'cookies' not in self.browserid_namespaces:
            raise BrowserIdManagerErr(
                'Cookies are not now being used as a browser id namespace, '
                'thus the browserid cookie cannot be flushed.'
            )
        self._setCookie('deleted', self.REQUEST, remove=1)

    @security.protected(access_contents_information)
    def setBrowserIdCookieByForce(self, bid):
        """ See IBrowserIdManager.
        """
        if 'cookies' not in self.browserid_namespaces:
            raise BrowserIdManagerErr(
                'Cookies are not now being used as a browser id namespace, '
                'thus the browserid cookie cannot be forced.'
            )
        self._setCookie(bid, self.REQUEST)

    @security.protected(access_contents_information)
    def getHiddenFormField(self):
        """ See IBrowserIdManager.
        """
        s = '<input type="hidden" name="%s" value="%s" />'
        return s % (self.getBrowserIdName(), self.getBrowserId())

    @security.protected(access_contents_information)
    def encodeUrl(self, url, style='querystring', create=1):
        # See IBrowserIdManager
        bid = self.getBrowserId(create)
        if bid is None:
            raise BrowserIdManagerErr('There is no current browser id.')
        name = self.getBrowserIdName()
        if style == 'querystring':  # encode bid in querystring
            if '?' in url:
                return '%s&amp;%s=%s' % (url, name, bid)
            else:
                return '%s?%s=%s' % (url, name, bid)
        else:  # encode bid as first two URL path segments
            proto, host, path, params, query, frag = urlparse(url)
            path = '/%s/%s%s' % (name, bid, path)
            return urlunparse((proto, host, path, params, query, frag))

    # Non-IBrowserIdManager accessors / mutators.
    @security.protected(change_browser_id_managers)
    def setBrowserIdName(self, k):
        """ Set browser id name string

        o Enforce "valid" values.
        """
        if not (isinstance(k, str) and k and not badidnamecharsin(k)):
            raise BrowserIdManagerErr(
                'Bad id name string %s' % escape(repr(k))
            )
        self.browserid_name = k

    @security.protected(change_browser_id_managers)
    def setBrowserIdNamespaces(self, ns):
        """
        accepts list of allowable browser id namespaces
        """
        for name in ns:
            if name not in ALLOWED_BID_NAMESPACES:
                raise BrowserIdManagerErr(
                    'Bad browser id namespace %s' % repr(name)
                )
        self.browserid_namespaces = tuple(ns)

    @security.protected(access_contents_information)
    def getBrowserIdNamespaces(self):
        """ """
        return self.browserid_namespaces

    @security.protected(change_browser_id_managers)
    def setCookiePath(self, path=''):
        """ sets cookie 'path' element for id cookie """
        if not (isinstance(path, str) and not badcookiecharsin(path)):
            raise BrowserIdManagerErr(
                'Bad cookie path %s' % escape(repr(path))
            )
        self.cookie_path = path

    @security.protected(access_contents_information)
    def getCookiePath(self):
        """ """
        return self.cookie_path

    @security.protected(change_browser_id_managers)
    def setCookieLifeDays(self, days):
        """ offset for id cookie 'expires' element """
        if not isinstance(days, (int, float)):
            raise BrowserIdManagerErr(
                'Bad cookie lifetime in days %s '
                '(requires integer value)' % escape(repr(days))
            )
        self.cookie_life_days = int(days)

    @security.protected(access_contents_information)
    def getCookieLifeDays(self):
        """ """
        return self.cookie_life_days

    @security.protected(change_browser_id_managers)
    def setCookieDomain(self, domain):
        """ sets cookie 'domain' element for id cookie """
        if not isinstance(domain, str):
            raise BrowserIdManagerErr(
                'Cookie domain must be string: %s' % escape(repr(domain))
            )
        if not domain:
            self.cookie_domain = ''
            return
        if not twodotsin(domain):
            raise BrowserIdManagerErr(
                'Cookie domain must contain at least two dots '
                '(e.g. ".zope.org" or "www.zope.org") or it must '
                'be left blank. : ' '%s' % escape(repr(domain))
            )
        if badcookiecharsin(domain):
            raise BrowserIdManagerErr(
                'Bad characters in cookie domain %s'
                % escape(repr(domain))
            )
        self.cookie_domain = domain

    @security.protected(access_contents_information)
    def getCookieDomain(self):
        """ """
        return self.cookie_domain

    @security.protected(change_browser_id_managers)
    def setCookieHTTPOnly(self, http_only):
        """ sets cookie 'HTTPOnly' on or off """
        self.cookie_http_only = bool(http_only)

    @security.protected(access_contents_information)
    def getCookieHTTPOnly(self):
        """ retrieve the 'HTTPOnly' flag """
        return self.cookie_http_only

    @security.protected(change_browser_id_managers)
    def setCookieSecure(self, secure):
        """ sets cookie 'secure' element for id cookie """
        self.cookie_secure = not not secure

    @security.protected(access_contents_information)
    def getCookieSecure(self):
        """ """
        return self.cookie_secure

    @security.protected(change_browser_id_managers)
    def setAutoUrlEncoding(self, auto_url_encoding):
        """ sets 'auto url encoding' on or off """
        self.auto_url_encoding = not not auto_url_encoding

    @security.protected(access_contents_information)
    def getAutoUrlEncoding(self):
        """ """
        return self.auto_url_encoding

    @security.protected(access_contents_information)
    def isUrlInBidNamespaces(self):
        """ Returns true if 'url' is in the browser id namespaces
        for this browser id """
        return 'url' in self.browserid_namespaces

    def _setCookie(
        self,
        bid,
        REQUEST,
        remove=0,
        now=time.time,
        strftime=time.strftime,
        gmtime=time.gmtime
    ):
        """ """
        expires = None
        if remove:
            expires = "Sun, 10-May-1971 11:59:00 GMT"
        elif self.cookie_life_days:
            expires = now() + self.cookie_life_days * 86400
            # Wdy, DD-Mon-YYYY HH:MM:SS GMT
            expires = strftime('%a %d-%b-%Y %H:%M:%S GMT', gmtime(expires))

        # cookie attributes managed by BrowserIdManager
        d = {
            'domain': self.cookie_domain,
            'path': self.cookie_path,
            'secure': self.cookie_secure,
            'http_only': self.cookie_http_only,
            'expires': expires,
        }

        if self.cookie_secure:
            URL1 = REQUEST.get('URL1', None)
            if URL1 is None:
                return  # should we raise an exception?
            if URL1.split(':')[0] != 'https':
                return  # should we raise an exception?

        cookies = REQUEST.RESPONSE.cookies
        cookie = cookies[self.browserid_name] = {}
        for k, v in d.items():
            if v:
                cookie[k] = v  # only stuff things with true values
        cookie['value'] = bid

    def _setId(self, id):
        if id != self.id:
            raise ValueError('Cannot rename a browser id manager')

    # Jukes for handling URI-munged browser IDS
    @security.private
    def hasTraversalHook(self, parent):
        name = TRAVERSAL_APPHANDLE
        return not not queryBeforeTraverse(parent, name)

    @security.private
    def updateTraversalData(self):
        if 'url' in self.browserid_namespaces:
            self.registerTraversalHook()
        else:
            self.unregisterTraversalHook()

    @security.private
    def unregisterTraversalHook(self):
        parent = aq_parent(aq_inner(self))
        name = TRAVERSAL_APPHANDLE
        if self.hasTraversalHook(parent):
            unregisterBeforeTraverse(parent, name)

    @security.private
    def registerTraversalHook(self):
        parent = aq_parent(aq_inner(self))
        if not self.hasTraversalHook(parent):
            hook = BrowserIdManagerTraverser()
            name = TRAVERSAL_APPHANDLE
            priority = 40  # "higher" priority than session data traverser
            registerBeforeTraverse(parent, hook, name, priority)

    # ZMI
    manage_options = (
        {
            'label': 'Settings',
            'action': 'manage_browseridmgr',
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

    def manage_afterAdd(self, item, container):
        """ Maybe add our traversal hook """
        self.updateTraversalData()

    def manage_beforeDelete(self, item, container):
        """ Remove our traversal hook if it exists """
        self.unregisterTraversalHook()

    security.declareProtected(view_management_screens,  # noqa: D001
                              'manage_browseridmgr')
    manage_browseridmgr = DTMLFile('dtml/manageIdManager', globals())

    @security.protected(change_browser_id_managers)
    def manage_changeBrowserIdManager(
        self,
        title='',
        idname='_ZopeId',
        location=('cookies', 'form'),
        cookiepath='/',
        cookiedomain='',
        cookielifedays=0,
        cookiesecure=0,
        cookiehttponly=0,
        auto_url_encoding=0,
        REQUEST=None
    ):
        """ """
        self.title = str(title)
        self.setBrowserIdName(idname)
        self.setCookiePath(cookiepath)
        self.setCookieDomain(cookiedomain)
        self.setCookieLifeDays(cookielifedays)
        self.setCookieSecure(cookiesecure)
        self.setCookieHTTPOnly(cookiehttponly)
        self.setBrowserIdNamespaces(location)
        self.setAutoUrlEncoding(auto_url_encoding)
        self.updateTraversalData()
        if REQUEST is not None:
            msg = '/manage_browseridmgr?manage_tabs_message=Changes saved'
            REQUEST.RESPONSE.redirect(self.absolute_url() + msg)


InitializeClass(BrowserIdManager)


class BrowserIdManagerTraverser(Persistent):

    def __call__(
        self,
        container,
        request,
        browser_id=None,
        browser_id_ns=None,
        BROWSERID_MANAGER_NAME=BROWSERID_MANAGER_NAME
    ):
        """
        Registered hook to set and get a browser id in the URL.  If
        a browser id is found in the URL of an  incoming request, we put it
        into a place where it can be found later by the browser id manager.
        If our browser id manager's auto-url-encoding feature is on, cause
        Zope-generated URLs to contain the browser id by rewriting the
        request._script list.
        """
        browser_id_manager = getattr(container, BROWSERID_MANAGER_NAME, None)
        # fail if we cannot find a browser id manager (that means this
        # instance has been "orphaned" somehow)
        if browser_id_manager is None:
            LOG.error('Could not locate browser id manager!')
            return

        try:
            stack = request['TraversalRequestNameStack']
            request.browser_id_ns_ = browser_id_ns
            bid_name = browser_id_manager.getBrowserIdName()

            # stuff the browser id and id namespace into the request
            # if the URL has a browser id name and browser id as its first
            # two elements.  Only remove these elements from the
            # traversal stack if they are a "well-formed pair".
            if len(stack) >= 2 and stack[-1] == bid_name:
                if isAWellFormedBrowserId(stack[-2]):
                    stack.pop()  # pop the name off the stack
                    browser_id = stack.pop()  # pop id off the stack
                    request.browser_id_ = browser_id
                    request.browser_id_ns_ = 'url'

            # if the browser id manager is set up with 'auto url encoding',
            # cause generated URLs to be encoded with the browser id name/value
            # pair by munging request._script.
            if browser_id_manager.getAutoUrlEncoding():
                if browser_id is None:
                    request.browser_id_ = browser_id = getNewBrowserId()
                request._script.append(quote(bid_name))
                request._script.append(quote(browser_id))
        except Exception:
            LOG.error('indeterminate error', exc_info=sys.exc_info())


if six.PY2:
    import string

    b64_trans = string.maketrans('+/', '-.')
    b64_untrans = string.maketrans('-.', '+/')

    def getB64TStamp(
        b2a=binascii.b2a_base64,
        gmtime=time.gmtime,
        time=time.time,
        b64_trans=b64_trans,
        split=string.split,
        TimeStamp=TimeStamp.TimeStamp,
        translate=string.translate
    ):
        t = time()
        ts = split(
            b2a(TimeStamp(*gmtime(t)[:5] + (t % 60, )).raw())[:-1],
            '=')[0]
        return translate(ts, b64_trans)

    def getB64TStampToInt(
        ts,
        TimeStamp=TimeStamp.TimeStamp,
        b64_untrans=b64_untrans,
        a2b=binascii.a2b_base64,
        translate=string.translate
    ):
        return TimeStamp(a2b(translate(ts + '=', b64_untrans))).timeTime()

else:
    def getB64TStamp(
        b2a=binascii.b2a_base64,
        gmtime=time.gmtime,
        time=time.time,
        TimeStamp=TimeStamp.TimeStamp,
    ):
        t = time()
        stamp = TimeStamp(*gmtime(t)[:5] + (t % 60,))
        ts = b2a(stamp.raw()).split(b'=')[:-1][0]
        return ts.replace(b'/', b'.').replace(b'+', b'-').decode('ascii')

    def getB64TStampToInt(
        ts,
        TimeStamp=TimeStamp.TimeStamp,
        a2b=binascii.a2b_base64
    ):
        stamp = TimeStamp(a2b(ts.replace('.', '/').replace('-', '+') + '='))
        return stamp.timeTime()


def getBrowserIdPieces(bid):
    """returns browser id parts in a tuple consisting of rand_id,
    timestamp
    """
    return (bid[:8], bid[8:19])


def isAWellFormedBrowserId(bid, binerr=binascii.Error):
    try:
        rnd, ts = getBrowserIdPieces(bid)
        int(rnd)
        getB64TStampToInt(ts)
        return bid
    except (TypeError, ValueError, AttributeError, IndexError, binerr):
        return None


def getNewBrowserId(randint=_randint, maxint=99999999):
    """Returns 19-character string browser id
    'AAAAAAAABBBBBBBB'
    where:

    A == leading-0-padded 8-char string-rep'd random integer
    B == modified base64-encoded 11-char timestamp

    To be URL-compatible, base64 encoding is modified as follows:
      '=' end-padding is stripped off
      '+' is translated to '-'
      '/' is translated to '.'

    An example is: 89972317A0C3EHnUi90w
    """
    return '%08i%s' % (randint(0, maxint - 1), getB64TStamp())
