.. image:: https://github.com/zopefoundation/Products.Sessions/actions/workflows/tests.yml/badge.svg
        :target: https://github.com/zopefoundation/Products.Sessions/actions/workflows/tests.yml

.. image:: https://coveralls.io/repos/github/zopefoundation/Products.Sessions/badge.svg?branch=master
   :target: https://coveralls.io/github/zopefoundation/Products.Sessions?branch=master

.. image:: https://img.shields.io/pypi/v/Products.Sessions.svg
   :target: https://pypi.org/project/Products.Sessions/
   :alt: Current version on PyPI

.. image:: https://img.shields.io/pypi/pyversions/Products.Sessions.svg
   :target: https://pypi.org/project/Products.Sessions/
   :alt: Supported Python versions

Overview
========

Zope server side session management.

This package contains ``Products.Sessions`` and ``Products.Transience``.

Please note
-----------
Before release 5.2 of the ``tempstorage`` package sessioning configurations
using the simple temporary folder implementation shown below were discouraged
because the temporary storage backend could lose data. This is no longer the
case.

Using sessions with Zope
------------------------
For simple RAM memory-based sessioning support, suitable for smaller
deployments with a single Zope application server instance, add or uncomment
the following temporary storage database definition in your Zope configuration
file::

  <zodb_db temporary>
      <temporarystorage>
        name Temporary database (for sessions)
      </temporarystorage>
      mount-point /temp_folder
      container-class Products.TemporaryFolder.TemporaryContainer
  </zodb_db>

After a Zope restart, visit the Zope Management Interface and select
ZODB Mount Point from the list of addable items to instantiate the temporary
folder mount point. This only needs to be done once. After that point the
``temp_folder`` object will be recreated on each Zope restart and the session
support will automatically put a session data container into the temporary
folder.

For more advanced scenarios see the `Zope book chapter on Session management
<https://zope.readthedocs.io/en/latest/zopebook/Sessions.html#alternative-server-side-session-backends-for-zope-4>`_.
