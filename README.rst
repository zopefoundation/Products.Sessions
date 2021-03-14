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


Using sessions under Zope 4
---------------------------
The default session support under Zope 2 relied on ``Products.TemporaryFolder``
for storing session data, which in turn used the ``tempstorage`` package.
``tempstorage`` is no longer recommended because it has unfixed and possibly
unfixable issues under Zope 4 that lead to corrupted temporary storages.

If you use sessions sparingly and don't write to them often, a quick workaround
is to remove the existing ``/temp_folder`` instance in the ZODB if it still is
a `Temporary Folder` and create a normal `Folder` object named ``temp_folder``
in its stead. Inside that new ``/temp_folder``, create a
`Transient Object Container` with the ID ``session_data``. Now session data
will be stored in the main ZODB.

If you use sessions heavily, or if the workaround above leads to an
unacceptable number of ZODB conflict errors, you should either try using
cookies or local browser storage via Javascript for storing session data, or 
switch to a different session implementation that does not store session data
in the ZODB at all. See `the Zope book on Sessions for details 
<https://zope.readthedocs.io/en/latest/zopebook/Sessions.html#alternative-server-side-session-backends-for-zope-4>`_.


Using sessions under Zope 2
---------------------------
If you use the standard Zope session implementation, don't forget to add
or uncomment the temporary storage database definition in your Zope
configuration::

  <zodb_db temporary>
      <temporarystorage>
        name Temporary database (for sessions)
      </temporarystorage>
      mount-point /temp_folder
      container-class Products.TemporaryFolder.TemporaryContainer
  </zodb_db>
