from functools import partial, wraps

from psycopg2 import connect as _connect
from psycopg2.extensions import register_adapter
from spans import *

from ._utils import adapt_range, register_range_caster, query_range_oids, floatrange_preprocess

__version__ = "0.1.1"

__all__ = [
    "connect",
    "register_range_type"
]

@wraps(_connect)
def connect(*keys, **kwargs):
    conn = _connect(*keys, **kwargs)

    if conn.server_version < 90200:
        raise RuntimeError("Range types not available in version {version}".format(
            conn.server_version))

    # Register range types
    register_range_caster(
        "int4range", intrange, oid=3904, subtype_oid=23, array_oid=3905, scope=conn)
    register_range_caster(
        "int8range", intrange, oid=3926, subtype_oid=20, array_oid=3927, scope=conn)
    register_range_caster(
        "numrange", floatrange_preprocess, oid=3906, subtype_oid=1700, array_oid=3907, scope=conn)
    register_range_caster(
        "daterange", daterange, oid=3912, subtype_oid=1082, array_oid=3913, scope=conn)
    register_range_caster(
        "tsrange", datetimerange, oid=3908, subtype_oid=1114, array_oid=3909, scope=conn)

    return conn

def register_range_type(pgrange, pyrange, conn):
    """
    Register a new range type as a PostgreSQL range.

        >>> register_range_type("int4range", intrange, conn)

    The above will make sure intrange is regarded as an int4range for queries
    and that int4ranges will be cast into intrange when fetching rows.

    pgrange should be the full name including schema for the custom range type.

    Note that adaption is global, meaning if a range type is passed to a regular
    psycopg2 connection it will adapt it to its proper range type. Parsing of
    rows from the database however is not global and just set on a per connection
    basis.
    """

    register_adapter(pyrange, partial(adapt_range, pgrange))
    register_range_caster(
        pgrange, pyrange, *query_range_oids(pgrange, conn), scope=conn)

register_adapter(intrange, partial(adapt_range, "int4range"))
register_adapter(floatrange, partial(adapt_range, "numrange"))
register_adapter(daterange, partial(adapt_range, "daterange"))
register_adapter(datetimerange, partial(adapt_range, "tsrange"))
