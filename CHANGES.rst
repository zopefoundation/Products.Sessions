Changelog
=========

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
