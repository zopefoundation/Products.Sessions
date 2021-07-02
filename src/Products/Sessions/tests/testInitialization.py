##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

import os
import shutil
import tempfile
import unittest

import Products
from App.config import getConfiguration
from App.config import setConfiguration
from OFS.Application import AppInitializer
from OFS.Application import Application
from Zope2.Startup.options import ZopeWSGIOptions


test_cfg = """
instancehome {instancehome}

<zodb_db main>
   mount-point /
   <mappingstorage>
      name mappingstorage
   </mappingstorage>
</zodb_db>

<zodb_db temporary>
    # Temporary storage database (for sessions)
    <temporarystorage>
      name temporary storage for sessioning
    </temporarystorage>
    mount-point /temp_folder
    container-class OFS.Folder.Folder
</zodb_db>
"""


def getApp():
    from App.ZApplication import ZApplicationWrapper
    DB = getConfiguration().dbtab.getDatabase('/')
    return ZApplicationWrapper(DB, 'Application', Application)()


class TestInitialization(unittest.TestCase):
    """Test the application initialization."""

    def setUp(self):
        self.original_config = getConfiguration()
        self.TEMPDIR = tempfile.mkdtemp()

    def tearDown(self):
        setConfiguration(self.original_config)
        shutil.rmtree(self.TEMPDIR)
        Products.__path__ = [d
                             for d in Products.__path__
                             if os.path.exists(d)]

    def configure(self, text):
        # We have to create a directory of our own since the existence
        # of the directory is checked.  This handles this in a
        # platform-independent way.
        config_path = os.path.join(self.TEMPDIR, 'zope.conf')
        with open(config_path, 'w') as fd:
            fd.write(text.format(instancehome=self.TEMPDIR))

        options = ZopeWSGIOptions(config_path)()
        config = options.configroot
        self.assertEqual(config.instancehome, self.TEMPDIR)
        setConfiguration(config)

    def getInitializer(self):
        app = getApp()
        return AppInitializer(app)

    def test_install_browser_id_manager(self):
        from Products.Sessions.BrowserIdManager import BrowserIdManager
        self.configure(test_cfg)
        initializer = self.getInitializer()
        app = initializer.getApp()
        initializer.install_products()
        self.assertIsInstance(app.browser_id_manager, BrowserIdManager)
        self.assertEqual(app.browser_id_manager.meta_type,
                         'Browser Id Manager')

    def test_install_session_data_manager(self):
        from Products.Sessions.SessionDataManager import SessionDataManager
        self.configure(test_cfg)
        initializer = self.getInitializer()
        initializer.install_products()
        app = initializer.getApp()
        self.assertIsInstance(app.session_data_manager, SessionDataManager)
        self.assertEqual(app.session_data_manager.meta_type,
                         'Session Data Manager')
