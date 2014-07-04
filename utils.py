#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import psycopg2

import conf

POINT_QUERY_SQL = """
SELECT
    %s AS lon,
    %s AS lat,
    rast.filename,
    ST_Value(rast.rast, ST_SetSRID(ST_Make#Point(%s, %s), 4326))
FROM <<TABLE_NAME>> AS rast
WHERE ST_Intersects(ST_SetSRID(ST_MakePoint(%s, %s), 4326), rast.rast)
AND rast.filename IN %s;
"""

POINT_IN_POLYGON_SQL = """
SELECT
    <<FIELD>>
FROM <<TABLE_NAME>>
WHERE ST_Contains(
    geom,
    ST_GeomFromText('POINT(%s %s)', 4326)
);
"""

GET_BUFFER_AT_POINT = """
SELECT * from buffers_for_raster WHERE id = %s;
"""


SET_BUFFER_AT_POINT_SQL = """
INSERT INTO points_for_buffer(id, lat, lng, geom)
    VALUES(%s, %s, %s, ST_GeomFromText('POINT(%s %s)', 4326));

INSERT INTO buffers_for_raster(id, geom)
    SELECT id, ST_Buffer(geom, %s) FROM points_for_buffer
    WHERE id = %s;
"""

SET_CUSTOM_BUFFER_AT_POINT_SQL = """
INSERT INTO points_for_buffer(id, lat, lng, geog)
    VALUES(%s, %s, %s, ST_GeogFromText('SRID=4326;POINT(%s %s)'));

INSERT INTO buffers_for_raster(id, geog)
    SELECT id, ST_Buffer(geog, %s) FROM points_for_buffer
    WHERE id = %s;
"""

DELETE_BUFFER_AT_POINT_SQL = """
DELETE FROM points_for_buffer
      WHERE id=%s;

DELETE FROM buffers_for_raster
      WHERE id=%s;
"""

BUFFER_QUERY_SQL = """
SELECT id, CAST(AVG(((foo.geomval).val)) AS decimal(9,3)) as avgimr
FROM (
    SELECT b.id, ST_Intersection(<<TABLE_NAME>>.rast, b.geom) AS geomval
    FROM <<TABLE_NAME>>, buffers_for_raster b
    WHERE ST_Intersects(b.geom, <<TABLE_NAME>>.rast)
) AS foo
WHERE id = %s
GROUP BY id
ORDER BY id;
"""

CUSTOM_BUFFER_QUERY_SQL = """
SELECT id, CAST(AVG(((foo.geomval).val)) AS decimal(9,3)) as avgimr
FROM (
    SELECT b.id, ST_Intersection(<<TABLE_NAME>>.rast, b.geog::geometry) AS geomval
    FROM <<TABLE_NAME>>, buffers_for_raster b
    WHERE ST_Intersects(b.geog::geometry, <<TABLE_NAME>>.rast)
) AS foo
WHERE id = %s
GROUP BY id
ORDER BY id;
"""


def get_conn_cur():
    """DB setup shortcut."""
    conn = psycopg2.connect(
        dbname=conf.DBNAME,
        user=conf.USER,
        host=conf.HOST,
        password=conf.PASSWORD
    )
    cur = conn.cursor()
    return conn, cur

def with_connection(fn):
    def wrapped(*args, **kwargs):
        connection = None
        result = None
        try:
            connection, cursor = get_conn_cur()
            result = fn(connection, cursor, *args, **kwargs)
        finally:
            if connection:
                connection.close()
        return result
    return wrapped

@with_connection
def get_point_in_polygon_value(conn, cur, point, table, field, explain=False):
    """
    Given a lat-lon point and a PostGIS table, get the field value
    of the polygon that contains the point.
    """
    row = ''
    sql = POINT_IN_POLYGON_SQL.replace(
        "<<TABLE_NAME>>", table).replace(
        "<<FIELD>>", field)
    explanation = [] if explain else False

    lat = float(point.get('lat'))
    lon = float(point.get('lon'))
    cur.execute(sql, (lon, lat))
    if explain:
        explanation.append(cur.mogrify(sql, (lon, lat)))
    values = cur.fetchall()
    value = values[0][0] if len(values) > 0 else ''
    row = [field, value]

    if explain:
        explanation = "\n".join(explanation)
    return row, explanation

@with_connection
def get_value_at_points(conn, cur, points, tifs=None, explain=False):
    """Get the value at the points for the tifs"""
    tifs = tifs or []

    sql = POINT_QUERY_SQL.replace(
        "<<TABLE_NAME>>",
        conf.TABLE
    )

    explanation = [] if explain else False
    rows = []

    # lazily, for now...
    for lon, lat in points:
        cur.execute(sql, (lon, lat, lon, lat, lon, lat, tifs))
        if explain:
            explanation.append(
                cur.mogrify(sql, (lon, lat, lon, lat, lon, lat, tifs)))
        rows.extend(cur.fetchall())

    if explain:
        explanation = "\n".join(explanation)
    return rows, explanation


@with_connection
def set_buffer_at_point(conn, cur, point, buf=25, custom_buffer=False):
    """
    Checks if a buffer geometry exists for the current point and if not
    it creates it.
    """

    #  Hard lock at a 25km buffer, specified here as Geometry value
    #  not geography value. 
    #  buf = 25km / 111.13  # one degree ish, varying about the equator..
    if not custom_buffer:
        buf = 0.2249
    else:
        # Convert km to metres. We'll use geography rather than geometry
        buf = buf * 1000

    # point is (lng, lat, id)
    lat = float(point[1])
    lng = float(point[0])
    id = point[2]

    conn.autocommit = True

    # Delete existing buffer
    cur.execute(DELETE_BUFFER_AT_POINT_SQL, (id, id))

    # Create the buffer
    if custom_buffer:
        cur.execute(SET_CUSTOM_BUFFER_AT_POINT_SQL, (id, lat, lng, lng, lat, buf, id))
    else:
        cur.execute(SET_BUFFER_AT_POINT_SQL, (id, lat, lng, lng, lat, buf, id))

@with_connection
def get_buffer_value_at_point(conn, cur, buf, point, raster, explain=False, custom_buffer=False):
    """Get a buffer of approx bufKM around point (lon, lat) in raster."""
    # point is (lng, lat, id)
    set_buffer_at_point(point, buf, custom_buffer=custom_buffer)
    SQL = BUFFER_QUERY_SQL
    if custom_buffer:
        SQL = CUSTOM_BUFFER_QUERY_SQL
    sql = SQL.replace("<<TABLE_NAME>>", raster)
    explanation = False
    id = point[2]
    cur.execute(sql, (id,))
    if explain:
        explanation = cur.mogrify(sql, (id,))
    result = cur.fetchall()

    return result, explanation
