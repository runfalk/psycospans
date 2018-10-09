import datetime as dt
import os

from functools import partial
from psycopg2._psycopg import ProgrammingError, InternalError
from spans import *
from unittest import TestCase, skipUnless

from psycospans import *
from psycospans._utils import *

def build_test_dsn():
    dbname = os.environ.get("PGDATABASE", "psycospans_test")
    dbhost = os.environ.get("PGHOST", None)
    dbport = os.environ.get("PGPORT", None)
    dbuser = os.environ.get("PGUSER", None)
    dbpass = os.environ.get("PGPASSWORD", None)

    dsn = ["dbname=" + dbname]

    if dbhost is not None:
        dsn.append("host=" + dbhost)

    if dbport is not None:
        dsn.append("port=" + dbport)

    if dbuser is not None:
        dsn.append("user=" + dbuser)

    if dbpass is not None:
        dsn.append("password=" + dbpass)

    return " ".join(dsn)

def can_connect():
    try:
        cnn = connect(build_test_dsn())
    except:
        return False
    else:
        cnn.close()
        return True

class TestCasting(TestCase):
    def test_parse_raw_range_string(self):
        self.assertEqual(
            parse_raw_range_string("empty"), empty_rawrange)

        self.assertEqual(
            parse_raw_range_string("[,)"), raw_range(None, None, True, False))
        self.assertEqual(
            parse_raw_range_string("(,)"), raw_range(None, None, False, False))
        self.assertEqual(
            parse_raw_range_string("(,]"), raw_range(None, None, False, True))
        self.assertEqual(
            parse_raw_range_string("[,]"), raw_range(None, None, True, True))

        self.assertEqual(
            parse_raw_range_string("[1, )"), raw_range("1", None, True, False))
        self.assertEqual(
            parse_raw_range_string("[, 2]"), raw_range(None, "2", True, True))
        self.assertEqual(
            parse_raw_range_string("(3, 4)"), raw_range("3", "4", False, False))
        self.assertEqual(
            parse_raw_range_string("[3.5, 4.7)"), raw_range("3.5", "4.7", True, False))

        self.assertEqual(
            parse_raw_range_string(r"['\\, \' \\', 'test']"),
            raw_range("\\, ' \\", "test", True, True))
        self.assertEqual(
            parse_raw_range_string(r"['\\, \"\' \\', 1]"),
            raw_range("\\, \"' \\", "1", True, True))
        self.assertEqual(
            parse_raw_range_string(r"[1, '\\, \' \\']"),
            raw_range("1", "\\, ' \\", True, True))

    def test_adapt_range(self):
        with self.assertRaises(ValueError):
            adapt_range("int4range", None)

        self.assertEqual(
            adapt_range("int4range", intrange(1, 5)).getquoted(),
            b"int4range(1, 5, '[)')")

        self.assertEqual(
            adapt_range("numrange", floatrange(2.5, 10.25, False)).getquoted(),
            b"numrange(2.5, 10.25, '()')")

        self.assertEqual(
            adapt_range("daterange", daterange(
                dt.date(2013, 1, 1), dt.date(2013, 2, 15))).getquoted(),
            b"daterange('2013-01-01'::date, '2013-02-15'::date, '[)')")

        self.assertEqual(
            adapt_range(
                "tsrange",
                datetimerange(upper=dt.datetime(2013, 1, 1, 4, 50))).getquoted(),
            b"tsrange(NULL, '2013-01-01T04:50:00'::timestamp, '()')")

        self.assertEqual(
            adapt_range("int4range", intrange.empty()).getquoted(),
            b"'empty'::int4range")

@skipUnless(can_connect(), "No test database available")
class TestDatabase(TestCase):
    def setUp(self):
        self.conn = connect(build_test_dsn())

    def tearDown(self):
        self.conn.close()

    def test_intrange(self):
        cur = self.conn.cursor()
        test_range = intrange(1, 10)
        cur.execute("SELECT int4range(5, NULL), %s", (test_range,))

        self.assertEqual(
            cur.fetchone(),
            (intrange(5), test_range))

    def test_floatrange(self):
        cur = self.conn.cursor()
        test_range = floatrange(0.5, lower_inc=False)
        cur.execute("SELECT numrange(5.5, 10.25), %s", (test_range,))

        self.assertEqual(
            cur.fetchone(),
            (floatrange(5.5, 10.25), test_range))

    def test_daterange(self):
        cur = self.conn.cursor()
        test_range = daterange(dt.date(2013, 1, 1), dt.date(2013, 2, 15))
        cur.execute("SELECT daterange('2013-04-04'::date, NULL), %s", (test_range,))

        self.assertEqual(
            cur.fetchone(),
            (daterange(dt.date(2013, 4, 4)), test_range))

    def test_datetimerange(self):
        cur = self.conn.cursor()
        test_range = datetimerange(
            dt.datetime(2013, 1, 1, 10, 20, 30),
            dt.datetime(2013, 2, 15, 20, 30, 40),
            upper_inc=True)
        cur.execute("SELECT tsrange('2013-04-04 04:50:45'::timestamp, NULL), %s", (test_range,))

        self.assertEqual(
            cur.fetchone(),
            (datetimerange(dt.datetime(2013, 4, 4, 4, 50, 45)), test_range))

    def test_query_range_oids(self):
        q = partial(query_range_oids, conn_or_curs=self.conn)

        self.assertEqual(q("pg_catalog.int4range"), (3904, 23, 3905))
        self.assertEqual(q("pg_catalog.int8range"), (3926, 20, 3927))
        self.assertEqual(q("pg_catalog.numrange"), (3906, 1700, 3907))
        self.assertEqual(q("pg_catalog.daterange"), (3912, 1082, 3913))
        self.assertEqual(q("pg_catalog.tsrange"), (3908, 1114, 3909))

    def test_custom_range(self):
        cur = self.conn.cursor()

        # This may fail if the type already exists
        try:
            cur.execute("CREATE TYPE intervalrange AS RANGE(SUBTYPE = interval)")
        except ProgrammingError:
            self.conn.rollback()
        else:
            self.conn.commit()

        register_range_type("intervalrange", timedeltarange, self.conn)

        test_range = timedeltarange(dt.timedelta(1, 5), dt.timedelta(1, 10))
        cur.execute("SELECT intervalrange('1 day'::interval, NULL), %s", (test_range,))

        self.assertEqual(
            cur.fetchone(),
            (timedeltarange(dt.timedelta(1)), test_range))

        # This may fail if the type already existed before test
        try:
            cur.execute("DROP TYPE intervalrange")
        except InternalError:
            self.conn.rollback()
        else:
            self.conn.commit()
        self.conn.commit()
