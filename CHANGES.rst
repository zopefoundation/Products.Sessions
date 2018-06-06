Changelog
=========

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
