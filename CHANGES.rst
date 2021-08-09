Changelog
=========

4.12 (2021-08-09)
-----------------

- Fix PY2 bug in ``BrowserIdManager.getNewBrowserId``
  (`#45 <https://github.com/zopefoundation/Products.Sessions/issues/45>`_)


4.11 (2021-07-07)
-----------------

- Improve out-of-the-box experience by instantiating a session data container
  if the session data manager uses the default configuration that points
  to a temporary folder

- Reinstate simple sessioning with ``Products.TemporaryFolder``
  (`#43 <https://github.com/zopefoundation/Products.Sessions/issues/43>`_)


4.10 (2021-07-02)
-----------------

- Reduce usage of deprecated ``tempstorage`` for testing and remove warnings
  (`#41 <https://github.com/zopefoundation/Products.Sessions/issues/41>`_)


4.9 (2021-03-16)
----------------

- Add support for Python 3.9


4.8 (2020-08-21)
----------------

- Don't break completely when no session data container is available
  (`#35 <https://github.com/zopefoundation/Products.Sessions/issues/35>`_)


4.7 (2020-08-07)
----------------

- Make the product compatible with ``transaction`` version 3
  (`#32 <https://github.com/zopefoundation/Products.Sessions/issues/32>`_)


4.6 (2019-10-12)
----------------

- Banish dependency on ``Products.TemporaryFolder`` into a tests extra
  and point out its issues under Zope 4 in the README.
  (`#26 <https://github.com/zopefoundation/Products.Sessions/issues/26>`_)

- Switch tests dependencies to Zope 4.x branch to retain Python 2 compatibility

- Fix access permissions for ``meta_type`` and ``zmi_icon`` properties so
  they don't raise when accessed in the admin interface.
  (`#24 <https://github.com/zopefoundation/Products.Sessions/pull/24>`_)
  
- Fix Python 3 compatibility of ``_p_resolveConflict``.
  (`#25 <https://github.com/zopefoundation/Products.Sessions/pull/25>`_)


4.5 (2019-04-15)
----------------

- add badges to the README

- add additional links on PyPI


4.4 (2019-03-28)
----------------

- improve flake8 compliance

- Implement ``__contains__`` on ``TransientObject``
  (`#21 <https://github.com/zopefoundation/Products.Sessions/issues/21>`_)

- Fix session data manager edit form


4.3.2 (2019-03-07)
------------------

- Fix ``NameError`` in ``Products/Transience/Transience.py`` introduced in
  version 4.3.


4.3.1 (2019-03-07)
------------------

- Fix HTML of ``manageDataManager.dtml``.
  (`#22 <https://github.com/zopefoundation/Products.Sessions/pull/22>`_)

4.3 (2019-02-17)
----------------

- Specify supported Python versions using ``python_requires`` in setup.py
  (`Zope#481 <https://github.com/zopefoundation/Zope/issues/481>`_)

- Add support for Python 3.8


4.2.1 (2018-11-30)
------------------

- Make sure ``TransientObjectContainer.getTimeoutMinutes`` returns ints.
  (`#17 <https://github.com/zopefoundation/Products.Sessions/issues/17>`_)

- Add ``tox``-based testing for unit tests, code coverage and linting.

- Fix ZMI layout.
  (`#19 <https://github.com/zopefoundation/Products.Sessions/pull/19>`_)


4.2 (2018-11-06)
----------------

- Update the forms to Bootstrap ZMI.
  (`#8 <https://github.com/zopefoundation/Products.Sessions/pull/8>`_)

- Add support for Python 3.7.


4.1 (2018-06-06)
----------------

- Add support for Python 3.5 and 3.6.

- Quote variables in Products.Transience manage_container to avoid XSS.
  From Products.PloneHotfix20160830.

- Bring back Application initialization (creation of BrowserIdManager and
  SessionDataManager in the ZODB on first startup).
  This requires Zope >= 4.0b5.


4.0 (2016-07-23)
----------------

- Released as separate distribution including the code.
  This release requires Zope >= 4.0.


3.0 (2016-08-01)
----------------

- Create a separate distribution called `Products.Sessions` without
  any code inside it. This allows projects to depend on this project
  inside the Zope 2.13 release line.
