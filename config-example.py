import os


_basedir = os.path.abspath(os.path.dirname(__file__))

DEBUG = False

ADMINS = frozenset(['swdev@maplecroft.com'])
SECRET_KEY = ''

DATABASE = {
    'name': '',
    'host': '',
    'table': '',
    'user': '',
    'password': ''
}

SPATIAL_REFERENCE_ID = 4326
