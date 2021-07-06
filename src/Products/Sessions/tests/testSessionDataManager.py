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
import unittest
import warnings


tf_name = 'temp_folder'
idmgr_name = 'browser_id_manager'
toc_name = 'temp_transient_container'
sdm_name = 'session_data_manager'

stuff = {}


def _getDB(use_temporary_folder=False):
    import transaction
    from OFS.Application import Application
    db = stuff.get('db')
    if not db:
        from ZODB import DB
        from ZODB.DemoStorage import DemoStorage
        ds = DemoStorage()
        db = DB(ds, pool_size=60)
        conn = db.open()
        root = conn.root()
        app = Application()
        root['Application'] = app
        transaction.savepoint(optimistic=True)
        _populate(app, use_temporary_folder)
        stuff['db'] = db
        conn.close()
    return db


def _delDB():
    import transaction
    transaction.abort()
    del stuff['db']


def _populate(app, use_temporary_folder=False):
    import transaction
    from OFS.DTMLMethod import DTMLMethod
    from OFS.Folder import Folder

    from Products.TemporaryFolder.TemporaryFolder import MountedTemporaryFolder

    from ..BrowserIdManager import BrowserIdManager
    from ..SessionDataManager import SessionDataManager
    from Products.Transience.Transience import TransientObjectContainer
    bidmgr = BrowserIdManager(idmgr_name)
    if use_temporary_folder:
        tf = MountedTemporaryFolder(tf_name, title="Temporary Folder")
    else:
        tf = Folder(tf_name)
    toc = TransientObjectContainer(
        toc_name,
        title='Temporary '
        'Transient Object Container',
        timeout_mins=20
    )
    session_data_manager = SessionDataManager(
        id=sdm_name,
        path='/' + tf_name + '/' + toc_name,
        title='Session Data Manager',
        requestName='TESTOFSESSION'
    )

    try:
        app._delObject(idmgr_name)
    except (AttributeError, KeyError):
        pass

    try:
        app._delObject(tf_name)
    except (AttributeError, KeyError):
        pass

    try:
        app._delObject(sdm_name)
    except (AttributeError, KeyError):
        pass

    try:
        app._delObject('index_html')
    except (AttributeError, KeyError):
        pass

    app._setObject(idmgr_name, bidmgr)

    app._setObject(sdm_name, session_data_manager)

    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        app._setObject(tf_name, tf)
    transaction.commit()

    app.temp_folder._setObject(toc_name, toc)
    transaction.commit()

    # index_html necessary for publishing emulation for testAutoReqPopulate
    app._setObject('index_html', DTMLMethod('', __name__='foo'))
    transaction.commit()


class TestSessionManager(unittest.TestCase):

    def setUp(self):
        from Testing import makerequest
        db = _getDB()
        conn = db.open()
        root = conn.root()
        self.app = makerequest.makerequest(root['Application'])
        self.timeout = 1

    def tearDown(self):
        _delDB()
        self.app._p_jar.close()
        del self.app

    def test_initialization(self):
        from ..SessionDataManager import SessionDataManager
        sdm = SessionDataManager('testing')

        self.assertEqual(sdm.getId(), 'testing')
        self.assertEqual(sdm.title, '')
        self.assertFalse(sdm.getContainerPath())
        self.assertFalse(sdm.getRequestName())

        sdm2 = SessionDataManager('testing',
                                  title='Test Title',
                                  path='/foo/bar',
                                  requestName='SESS')
        self.assertEqual(sdm2.getId(), 'testing')
        self.assertEqual(sdm2.title, 'Test Title')
        self.assertEqual(sdm2.getContainerPath(), '/foo/bar')
        self.assertEqual(sdm2.getRequestName(), 'SESS')

    def test_manage_changeSDM(self):
        sdm = self.app.session_data_manager

        sdm.manage_changeSDM(title='Test Title',
                             path='/foo/bar',
                             requestName='SESS')
        self.assertEqual(sdm.title, 'Test Title')
        self.assertEqual(sdm.getContainerPath(), '/foo/bar')
        self.assertEqual(sdm.getRequestName(), 'SESS')

    def test_setTitle(self):
        sdm = self.app.session_data_manager

        sdm.setTitle(None)
        self.assertEqual(sdm.title, '')

        sdm.setTitle('')
        self.assertEqual(sdm.title, '')

        sdm.setTitle('foo')
        self.assertEqual(sdm.title, 'foo')

    def test_setContainerPath(self):
        from ..interfaces import SessionDataManagerErr

        sdm = self.app.session_data_manager

        sdm.setContainerPath()
        self.assertFalse(sdm.getContainerPath())

        sdm.setContainerPath('')
        self.assertFalse(sdm.getContainerPath())

        with self.assertRaises(SessionDataManagerErr):
            sdm.setContainerPath('\\_I_am_not_allowed')

        with self.assertRaises(SessionDataManagerErr):
            sdm.setContainerPath(99)

        sdm.setContainerPath('/foo/bar/baz')
        self.assertEqual(sdm.getContainerPath(), '/foo/bar/baz')

        sdm.setContainerPath(('', 'foo', 'bar', 'baz'))
        self.assertEqual(sdm.getContainerPath(), '/foo/bar/baz')

        sdm.setContainerPath(['', 'foo', 'bar', 'baz'])
        self.assertEqual(sdm.getContainerPath(), '/foo/bar/baz')

    def testHasId(self):
        self.assertTrue(
            self.app.session_data_manager.id == sdm_name
        )

    def testHasTitle(self):
        self.assertTrue(
            self.app.session_data_manager.title == 'Session Data Manager'
        )

    def testGetSessionDataNoCreate(self):
        sd = self.app.session_data_manager.getSessionData(0)
        self.assertTrue(sd is None)

    def testGetSessionDataCreate(self):
        from Products.Transience.Transience import TransientObject
        sd = self.app.session_data_manager.getSessionData(1)
        self.assertTrue(sd.__class__ is TransientObject)

    def testHasSessionData(self):
        self.app.session_data_manager.getSessionData()
        self.assertTrue(self.app.session_data_manager.hasSessionData())

    def testNotHasSessionData(self):
        self.assertTrue(not self.app.session_data_manager.hasSessionData())

    def testSessionDataWrappedInSDMandTOC(self):
        from Acquisition import aq_base
        sd = self.app.session_data_manager.getSessionData(1)
        sdm = aq_base(getattr(self.app, sdm_name))
        toc = aq_base(getattr(self.app.temp_folder, toc_name))

        self.assertTrue(aq_base(sd.aq_parent) is sdm)
        self.assertTrue(aq_base(sd.aq_parent.aq_parent) is toc)

    def testNewSessionDataObjectIsValid(self):
        from Acquisition import aq_base

        from Products.Transience.Transience import TransientObject

        sdType = type(TransientObject(1))
        sd = self.app.session_data_manager.getSessionData()
        self.assertTrue(type(aq_base(sd)) is sdType)
        self.assertTrue(not hasattr(sd, '_invalid'))

    def testBrowserIdIsSet(self):
        self.app.session_data_manager.getSessionData()
        mgr = getattr(self.app, idmgr_name)
        self.assertTrue(mgr.hasBrowserId())

    def testGetSessionDataByKey(self):
        sd = self.app.session_data_manager.getSessionData()
        mgr = getattr(self.app, idmgr_name)
        token = mgr.getBrowserId()
        bykeysd = self.app.session_data_manager.getSessionDataByKey(token)
        self.assertTrue(sd == bykeysd)

    def testBadExternalSDCPath(self):
        sdm = self.app.session_data_manager
        # fake out webdav
        sdm.REQUEST['REQUEST_METHOD'] = 'GET'
        sdm.setContainerPath('/fudgeffoloo')
        self.assertFalse(sdm.hasSessionDataContainer())
        self.assertIsNone(self.app.session_data_manager.getSessionData())

    def testInvalidateSessionDataObject(self):
        sdm = self.app.session_data_manager
        sd = sdm.getSessionData()
        sd['test'] = 'Its alive!  Alive!'
        sd.invalidate()
        self.assertTrue(not sdm.getSessionData().has_key('test'))  # NOQA: W601
        self.assertTrue('test' not in sdm.getSessionData())

    def testGhostUnghostSessionManager(self):
        import transaction
        sdm = self.app.session_data_manager
        transaction.commit()
        sd = sdm.getSessionData()
        sd.set('foo', 'bar')
        sdm._p_changed = None
        transaction.commit()
        self.assertTrue(sdm.getSessionData().get('foo') == 'bar')

    def testSubcommitAssignsPJar(self):
        global DummyPersistent  # so pickle can find it
        import transaction
        from Persistence import Persistent

        class DummyPersistent(Persistent):
            pass

        sd = self.app.session_data_manager.getSessionData()
        dummy = DummyPersistent()
        sd.set('dp', dummy)
        self.assertTrue(sd['dp']._p_jar is None)
        transaction.savepoint(optimistic=True)
        self.assertFalse(sd['dp']._p_jar is None)

    def testAqWrappedObjectsFail(self):
        import transaction
        from Acquisition import Implicit

        class DummyAqImplicit(Implicit):
            pass
        a = DummyAqImplicit()
        b = DummyAqImplicit()
        aq_wrapped = a.__of__(b)
        sd = self.app.session_data_manager.getSessionData()
        sd.set('foo', aq_wrapped)
        self.assertRaises(TypeError, transaction.commit)

    def testAutoReqPopulate(self):
        self.app.REQUEST['PARENTS'] = [self.app]
        self.app.REQUEST['URL'] = 'a'
        self.app.REQUEST.traverse('/')
        self.assertTrue('TESTOFSESSION' in self.app.REQUEST)

    def testUnlazifyAutoPopulated(self):
        from Acquisition import aq_base

        from Products.Transience.Transience import TransientObject

        self.app.REQUEST['PARENTS'] = [self.app]
        self.app.REQUEST['URL'] = 'a'
        self.app.REQUEST.traverse('/')
        sess = self.app.REQUEST['TESTOFSESSION']
        sdType = type(TransientObject(1))
        self.assertTrue(type(aq_base(sess)) is sdType)

    def testUsesDefaultSessionDataContainer(self):
        sdm = self.app.session_data_manager

        sdm.setContainerPath('/foo/bar')
        self.assertFalse(sdm.usesDefaultSessionDataContainer())

        sdm.setContainerPath('/temp_folder/session_data')
        self.assertTrue(sdm.usesDefaultSessionDataContainer())

    def testDefaultSessionDataContainerCreation(self):
        sdm = self.app.session_data_manager
        default_path = '/temp_folder/session_data'

        # At first the configuration does not use the defaults
        self.assertNotEqual(sdm.getContainerPath(), default_path)
        sdc = sdm._getSessionDataContainer()
        self.assertNotEqual(sdc.absolute_url_path(), default_path)
        with self.assertRaises(KeyError):
            self.app.unrestrictedTraverse(default_path)

        # Set the default, now a session data container will get created
        sdm.setContainerPath('/temp_folder/session_data')
        sdc = sdm._getSessionDataContainer()
        self.assertEqual(sdc.absolute_url_path(), default_path)
        self.app.unrestrictedTraverse(default_path)

    def testDefaultSessionDataContainerSettings(self):
        from ..SessionDataManager import default_sdc_settings

        sdm = self.app.session_data_manager

        self.assertEqual(sdm.getDefaultSessionDataContainerSettings(),
                         default_sdc_settings)

        new_settings = {
            'title': 'Foo title',
            'timeout_mins': 30,
            'addNotification': '/call/me',
            'delNotification': '/call/me/again',
            'limit': 500,
            'period_secs': 10,
        }
        sdm.manage_changeSDCDefaults(**new_settings)
        self.assertDictEqual(sdm.getDefaultSessionDataContainerSettings(),
                             new_settings)

        # Make sure the settings are applied
        sdm.setContainerPath('/temp_folder/session_data')
        sdc = sdm._getSessionDataContainer()
        self.assertEqual(sdc.getTimeoutMinutes(), 30)
        self.assertEqual(sdc.getPeriodSeconds(), 10)
        self.assertEqual(sdc.getSubobjectLimit(), 500)
        self.assertEqual(sdc.getAddNotificationTarget(), '/call/me')
        self.assertEqual(sdc.getDelNotificationTarget(), '/call/me/again')


class TestSessionManagerWithTemporaryFolder(unittest.TestCase):

    def setUp(self):
        from Testing import makerequest
        db = _getDB(use_temporary_folder=True)
        conn = db.open()
        root = conn.root()
        self.app = makerequest.makerequest(root['Application'])
        self.timeout = 1

    def tearDown(self):
        _delDB()
        self.app._p_jar.close()
        del self.app

    def testForeignObject(self):
        from ZODB.POSException import InvalidObjectReference
        self.assertRaises(InvalidObjectReference, self._foreignAdd)

    def _foreignAdd(self):
        import transaction
        ob = self.app.session_data_manager

        # we don't want to fail due to an acquisition wrapper
        ob = ob.aq_base

        # we want to fail for some other reason:
        sd = self.app.session_data_manager.getSessionData()
        sd.set('foo', ob)
        transaction.commit()
