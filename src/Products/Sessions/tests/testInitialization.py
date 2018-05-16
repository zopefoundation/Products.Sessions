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

from App.config import getConfiguration, setConfiguration
from OFS.Application import Application, AppInitializer
from Zope2.Startup.options import ZopeWSGIOptions

good_cfg = """
instancehome <<INSTANCE_HOME>>

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
   container-class Products.TemporaryFolder.TemporaryContainer
</zodb_db>
"""

original_config = None


def getApp():
    from App.ZApplication import ZApplicationWrapper
    DB = getConfiguration().dbtab.getDatabase('/')
    return ZApplicationWrapper(DB, 'Application', Application)()


class TestInitialization(unittest.TestCase):
    """ Test the application initialization """

    def setUp(self):
        global original_config
        if original_config is None:
            original_config = getConfiguration()
        self.TEMPNAME = tempfile.mkdtemp()

    def tearDown(self):
        import App.config
        App.config.setConfiguration(original_config)
        shutil.rmtree(self.TEMPNAME)
        import Products
        Products.__path__ = [d for d in Products.__path__
                             if os.path.exists(d)]

    def configure(self, text):
        # We have to create a directory of our own since the existence
        # of the directory is checked.  This handles this in a
        # platform-independent way.
        config_path = os.path.join(self.TEMPNAME, 'zope.conf')
        with open(config_path, 'w') as fd:
            fd.write(text.replace(u"<<INSTANCE_HOME>>", self.TEMPNAME))

        options = ZopeWSGIOptions(config_path)()
        config = options.configroot
        self.assertEqual(config.instancehome, self.TEMPNAME)
        setConfiguration(config)

    def getOne(self):
        app = getApp()
        return AppInitializer(app)

    def test_install_browser_id_manager(self):
        self.configure(good_cfg)
        i = self.getOne()
        app = i.getApp()
        i.install_products()
        self.assertEqual(app.browser_id_manager.meta_type,'Browser Id Manager')

    def test_install_session_data_manager(self):
        self.configure(good_cfg)
        i = self.getOne()
        i.install_products()
        app = i.getApp()
        self.assertEqual(app.session_data_manager.meta_type,
                         'Session Data Manager')
