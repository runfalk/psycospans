PsycoSpans
==========
Psycospans brings support for `Spans <https://github.com/runfalk/spans>`_ to
`Psycopg2 <http://initd.org/psycopg/>`_.

PsycopSpans work by wrapping psycopg2's ``connect()`` function and set the
connection up for handling Spans' range types.

.. code-block:: python

    from psycospans import connect

    conn = connect("dbname=test")
    cur = conn.cursor()

    test_range = intrange(1, 10)
    cur.execute("SELECT int4range(5, NULL), %s", (test_range,))

    other_range, test_range_cmp = cur.fetchone()

    test_range == test_range_cmp # True
    other_range == intrange(5) # True


Requirements
------------
Psycospans will only work with PostgreSQL 9.2 or later.


Installation
------------
Psycospans exists on PyPI. Note that you must install ``psycopg2`` manually.
This is because you may use either ``psycopg2`` or ``psycopg2-binary``.

::

    pip install psycospans psycopg2-binary


Documentation
-------------
For full doumentation please run ``pydoc psycospans`` from a shell.


Changelog
=========

Version 1.0.0
-------------
Released on 9th October 2018

- Added wheel
- Moved unit tests out of package
- Removed explicit dependency on ``psycopg2`` since one may want to use
  ``psycopg2-binary``
- Removed Python 3.3 support. Requires 2.7 or 3.4 or greater
- Removed Tox usage for development
- Use pytest to run test suite


Version 0.1.1
-------------
Released on 23rd August 2018

- Fixed compatibility issue with Psycopg >= 2.5
- Improved Python 3 compatibility


Version 0.1.0
-------------
Released on 12th June 2014

- Initial release
