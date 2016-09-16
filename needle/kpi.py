import collections


KPI = collections.namedtuple('KPI', (
    'name',
    'description',
    'metric',
    'sql',
))
