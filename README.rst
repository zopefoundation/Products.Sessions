.. image:: https://travis-ci.org/zopefoundation/Products.Sessions.svg?branch=master
   :target: https://travis-ci.org/zopefoundation/Products.Sessions

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
