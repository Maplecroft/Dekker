#!/usr/bin/env python 
# -*- coding: iso-8859-15 -*-
from flask import Flask
import simplejson as json
import psycopg2

import conf

app = Flask(__name__)

SQL = """
SELECT 
    %s AS lon, 
    %s AS lat,
    rast.filename,
    ST_Value(rast.rast, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
FROM """ + conf.TABLE + """ AS rast
WHERE ST_Intersects(ST_SetSRID(ST_MakePoint(%s, %s), 4326), rast.rast)
AND rast.filename = %s;
"""


@app.route('/point/<view>/<lon>/<lat>/')
def value_at_point(view, lon, lat):
    """Get the value at a lon, lat for a given view."""
    conn = psycopg2.connect(
        dbname=conf.DBNAME,
        user=conf.USER,
        host=conf.HOST,
        password=conf.PASSWORD)
    cur = conn.cursor()
    cur.execute(SQL, (lon, lat, lon, lat, lon, lat, view))
    result = cur.fetchone()

    return json.dumps(dict(zip(['lon', 'lat', 'view', 'value'], result)))

if __name__ == '__main__':
    app.debug = conf.DEBUG
    app.run()
