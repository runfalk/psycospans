PsycoSpans
==========
Psycospans brings support for Spans [#]_ to Psycopg2 [#]_. The Spans library
implements PostgreSQL's range types [#]_ in pure Python.

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
Psycospans exists on PyPI.

::

    pip install psycospans

Documentation
-------------
For full doumentation please run ``pydoc psycospans`` from a shell.

.. [#] https://github.com/runfalk/spans
.. [#] http://initd.org/psycopg/
.. [#] http://www.postgresql.org/docs/9.2/static/rangetypes.html
