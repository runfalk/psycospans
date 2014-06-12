from psycospans import *
from spans import *

from psycospans._utils import parse_raw_range_string, raw_range

print parse_raw_range_string(r"['\\, \' \\', 'test']")
print raw_range("\\, ' \\", "test", True, True)


conn = connect("user=ante dbname=nittei")
register_range_type("intervalrange", timedeltarange, conn)

cur = conn.cursor()

cur.execute("SELECT '[1 days, 5 days)'::intervalrange, '[2014-02-14,2014-03-16)'::daterange, %s;", (daterange(dt.date.today()),))


print cur.fetchone()
