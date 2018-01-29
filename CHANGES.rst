Changelog
=========

4.1 (unreleased)
----------------

- Fix startup and syntax in python3
  [pbauer]

- Quote variables in Products.Transience manage_container to avoid XSS.
  From Products.PloneHotfix20160830.  [maurits]


4.0 (2016-07-23)
----------------

- Released as separate distribution including the code.
  This release requires Zope >= 4.0.


3.0 (2016-08-01)
----------------

- Create a separate distribution called `Products.Sessions` without
  any code inside it. This allows projects to depend on this project
  inside the Zope 2.13 release line.
