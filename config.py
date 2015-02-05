import os


_basedir = os.path.abspath(os.path.dirname(__file__))

DEBUG = False

ADMINS = frozenset(['swdev@maplecroft.com'])
SECRET_KEY = ''

DATABASE = {
    'name': 'rasters',
    'host': 'localhost',
    'table': 'rasters',
    'user': 'rasters',
    'password': '1fishwithadish!'
}

SPATIAL_REFERENCE_ID = 4326
