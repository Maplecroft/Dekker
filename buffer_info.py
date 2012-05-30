#!/usr/bin/env python 
# -*- coding: iso-8859-15 -*-
from flask import Flask, abort, make_response, request

import simplejson as json
import psycopg2

import conf

app = Flask(__name__)

TEMP_TABLE_SQL = """
DROP TABLE IF EXISTS tmp_points;
CREATE TEMP TABLE tmp_points ("gid" int, "point" geometry);
INSERT INTO tmp_points ("gid", "point") VALUES
    <<VALUES_STATEMENTS>>
""" 

QUERY_SQL = """
SELECT
    gid, filename, lon, lat,
CAST(AVG(((buf.geomval).val)) AS decimal(9,7)) as avgimr
FROM (
    SELECT
        ST_X(p.point)::NUMERIC(9, 5) AS lon, 
        ST_Y(p.point)::NUMERIC(9, 5) AS lat,
        p.gid,
        sn.filename,
        ST_Intersection(sn.rast, ST_SetSRID(ST_Buffer(p.point, %s), %s)) AS geomval
    FROM rasters sn, tmp_points p
    WHERE ST_Intersects(ST_SetSRID(ST_Buffer(p.point, %s), %s), sn.rast)
    <<AND_STATEMENTS>>
) AS buf
WHERE (buf.geomval).val >= 0
GROUP BY filename, gid, lon, lat
ORDER BY filename, gid, lon, lat;
"""

def get_conn_cur():
    """DB setup shortcut."""
    conn = psycopg2.connect(
        dbname=conf.DBNAME,
        user=conf.USER,
        host=conf.HOST,
        password=conf.PASSWORD,
    )
    cur = conn.cursor()
    return conn, cur


def get_points_table(points):
    """Expects a list of (id, lat, lon) tuples, returns for use.

    """
    sql = TEMP_TABLE_SQL
    point_line = "(%s, ST_MakePoint(%s, %s))"
    # get the point line for every point
    lines = map(lambda v: point_line, points)
    # flatten list into values
    values = [val for point in points for val in point]
    sql = sql.replace(
        "<<VALUES_STATEMENTS>>",
        ",\n".join(lines))

    return sql, values


def get_buffer_value_at_points(buf, points, tifs=None):
    """Get a buffer of approx bufKM around point (lon, lat) in tif(s)."""
    tifs = tifs or []

    one_degree = 111.13  # ish, varying about the equator...
    buf_degrees = 1.0 / (one_degree / buf)
    
    stmts = []

    test_point = points[0]
    if len(test_point) == 2:  # then it has no ID
        points = [(n, p[0], p[1]) for n, p in enumerate(points)]

    sql, values = get_points_table(points)
    values.extend([buf_degrees, conf.SRID, buf_degrees, conf.SRID])
    stmts.append(sql)
    
    and_stmt = ""
    if len(tifs) > 0:
        and_stmt = "AND sn.filename IN %s"
        values.append(tifs)
    
    sql = QUERY_SQL.replace("<<AND_STATEMENTS>>", and_stmt)
    stmts.append(sql)

    conn, cur = get_conn_cur()
    cur.execute(";\n".join(stmts), values)
    result = cur.fetchall()
    conn.close()
    return result


@app.route('/buffer')
def buffer_value_at_point():
    """View to get average value in buffer around point."""
    
    buf = request.args.get('buffer')
    lon = request.args.get('lon')
    lat = request.args.get('lat')
    tif = tuple(request.args.getlist('tif'))

    if not lon or not lat or not len(tif):
        abort(400)
    
    rows = get_buffer_value_at_points(float(buf), [(lon, lat)], tif)
    result = [
        dict(zip(('gid', 'tif', 'lon', 'lat', 'value'), row)) for row in rows
    ]
   
    resp = make_response(json.dumps(result), 200)
    resp.headers['Content-Type'] = 'application/json'

    return resp


@app.errorhandler(400)
def bad_request(error):
    resp = make_response('buffer, lon, lat, and tif are all required parameters', 400)
    resp.headers['Content-Type'] = 'text/plain'
    return resp


if __name__ == '__main__':
    app.debug = conf.DEBUG
    app.run()
