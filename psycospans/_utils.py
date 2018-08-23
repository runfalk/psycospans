import re

from collections import namedtuple
from functools import partial
from psycopg2._psycopg import ProgrammingError
from psycopg2.extensions import AsIs, adapt, new_type, new_array_type, register_type, STATUS_IN_TRANSACTION
from psycopg2.extras import _solve_conn_curs

from spans.types import range_
from spans import floatrange

__all__ = [
    "raw_range",
    "empty_rawrange",
    "floatrange_preprocess",
    "parse_raw_range_string",
    "cast_raw_range_string",
    "register_range_caster",
    "adapt_range",
    "query_range_oids"
]

_raw_range = namedtuple("rawrange", ["lower", "upper", "lower_inc", "upper_inc", "empty"])
raw_range = partial(_raw_range, empty=False)
empty_rawrange = _raw_range(*([None] * 4), empty=True)

def _raw_token(scanner, token):
    return token

def _unquote_token(scanner, token):
    return token[1:-1].encode().decode("unicode_escape")

raw_range_scanner = re.Scanner([
    (r"(['\"])(?:[^\1\\]|\\.)*?\1", _unquote_token),
    (r"(\[|\]|\(|\)|,)", _raw_token),
    (r"[^\[\]\(\),\s]+", _raw_token),
    (r"\s+", None)
])

def parse_raw_range_string(range_):
    # An empty range needs special handling
    if range_ == "empty":
        return empty_rawrange

    # Try to parse string using regex scanner
    tokens = raw_range_scanner.scan(range_)[0]

    # NOTE: This assumes that the given range is well formed

    return raw_range(
        lower=tokens[1] if tokens[2] == "," else None,
        upper=tokens[-2] if tokens[-3] == "," else None,
        lower_inc=True if tokens[0] == "[" else False,
        upper_inc=True if tokens[-1] == "]" else False)

def cast_raw_range_string(pyrange, range_, cur=None, subtype_oid=None):
    # If we got NULL just roll with it and return None
    if range_ is None:
        return None

    raw_range = parse_raw_range_string(range_)

    if raw_range.empty:
        return pyrange.empty()

    lower = raw_range.lower
    upper = raw_range.upper

    # Try to cast the individual components if cursor and subtype oid are
    # provided. This should be the standard case
    if cur is not None and subtype_oid is not None:
        lower = cur.cast(subtype_oid, lower)
        upper = cur.cast(subtype_oid, upper)

    return pyrange(lower, upper, raw_range.lower_inc, raw_range.upper_inc)

def register_range_caster(pgrange, pyrange, oid, subtype_oid, array_oid, scope=None):
    # Create an adapter for this range type
    adapter = partial(cast_raw_range_string, pyrange, subtype_oid=subtype_oid)

    # Create types using adapter
    range_type = new_type((oid,), pgrange, adapter)
    range_array_type = new_array_type((array_oid,), pgrange, range_type)

    register_type(range_type, scope)
    register_type(range_array_type, scope)

def adapt_range(pgrange, pyrange):
    if not isinstance(pyrange, range_):
        raise ValueError((
            "Trying to adapt range {range.__class__.__name__} which does not "
            "extend base range type.").format(range=pyrange))

    if not pyrange:
        return AsIs("'empty'::" + pgrange)

    lower = b"NULL"
    if not pyrange.lower_inf:
        lower = adapt(pyrange.lower).getquoted()

    upper = b"NULL"
    if not pyrange.upper_inf:
        upper = adapt(pyrange.upper).getquoted()

    return AsIs(b"".join([
        pgrange,
        b"(",
        lower,
        b", ",
        upper,
        b", '",
        b"[" if pyrange.lower_inc else b"(",
        b"]" if pyrange.upper_inc else b")",
        b"')",
    ]).decode("utf8"))

    # return AsIs("{range}({lower}, {upper}, '{lower_inc}{upper_inc}')".format(
    #     range=pgrange,
    #     lower=lower,
    #     upper=upper,
    #     lower_inc="[" if pyrange.lower_inc else "(",
    #     upper_inc="]" if pyrange.upper_inc else ")"))

def query_range_oids(pgrange, conn_or_curs):
    conn, curs = _solve_conn_curs(conn_or_curs)

    # Store transaction status
    conn_status = conn.status

    # Calculate absolutre location for pgrange
    if "." in pgrange:
        schema, name = pgrange.split(".", 1)
    else:
        name = pgrange
        schema = "public"

    # Query oids
    try:
        curs.execute("""
            SELECT
                r.rngtypid,
                r.rngsubtype,
                t.typarray
            FROM pg_range r
                JOIN pg_type t ON(t.oid = r.rngtypid)
                JOIN pg_namespace ns ON(ns.oid = t.typnamespace)
            WHERE t.typname = %s AND ns.nspname = %s;
        """, (name, schema))
    except ProgrammingError:
        if not conn.autocommit:
            conn.rollback()
        raise

    type_data = curs.fetchone()

    # Reset status if it was tampered with
    if conn_status != STATUS_IN_TRANSACTION and not conn.autocommit:
        conn.rollback()

    if type_data is None:
        raise ProgrammingError("PostgreSQL type '{type}' not found".format(
            type=name))

    return type_data

def floatrange_preprocess(lower=None, upper=None, lower_inc=None, upper_inc=None):
    if lower is not None:
        lower = float(lower)

    if upper is not None:
        upper = float(upper)

    return floatrange(lower, upper, lower_inc, upper_inc)
