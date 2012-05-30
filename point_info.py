#!/usr/bin/env python 
# -*- coding: iso-8859-15 -*-
from flask import Flask, abort, make_response, request

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
AND rast.filename IN %s;
"""


@app.route('/point')
def value_at_point():
    """Get the value at a lon, lat for a given view."""
    lon = request.args.get('lon')
    lat = request.args.get('lat')
    tif = tuple(request.args.getlist('tif[]'))

    if not lon or not lat or not len(tif):
        abort(400)

    kwargs = dict(
        dbname=conf.DBNAME,
        user=conf.USER,
        host=conf.HOST,
        password=conf.PASSWORD,
    )

    rows = []
    try:
        conn = psycopg2.connect(**kwargs)
        cur = conn.cursor()
        cur.execute(SQL, (lon, lat, lon, lat, lon, lat, tif))
        rows = cur.fetchall()
    finally:
        conn.close()

    result = [
        dict(zip(('lon', 'lat', 'view', 'value'), row)) for row in rows
    ]

    resp = make_response(json.dumps(result), 200)
    resp.headers['Content-Type'] = 'application/json'

    return resp


@app.errorhandler(400)
def bad_request(error):
    resp = make_response('lon, lat, and tif are all required parameters', 400)
    resp.headers['Content-Type'] = 'text/plain'
    return resp


if __name__ == '__main__':
    app.debug = conf.DEBUG
    app.run()
