#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
import psycopg2

import conf


TEMP_TABLE_SQL = """
DROP TABLE IF EXISTS tmp_points;
CREATE TEMP TABLE tmp_points ("gid" int, "point" geometry);
INSERT INTO tmp_points ("gid", "point") VALUES
    <<VALUES_STATEMENTS>>
"""


BUFFER_QUERY_SQL = """
SELECT
    gid, filename, lon, lat,
CAST(AVG(((buf.geomval).val)) AS decimal(9,7)) as avgimr
FROM (
    SELECT
        ST_X(p.point)::NUMERIC(9, 5) AS lon,
        ST_Y(p.point)::NUMERIC(9, 5) AS lat,
        p.gid,
        rast.filename,
        ST_Intersection(rast.rast, ST_SetSRID(ST_Buffer(p.point, %s), %s)) AS geomval
    FROM <<TABLE_NAME>> rast, tmp_points p
    WHERE ST_Intersects(ST_SetSRID(ST_Buffer(p.point, %s), %s), rast.rast)
    <<AND_STATEMENTS>>
) AS buf
WHERE (buf.geomval).val >= 0
GROUP BY filename, gid, lon, lat
ORDER BY filename, gid, lon, lat;
"""


POINT_QUERY_SQL = """
SELECT
    %s AS lon,
    %s AS lat,
    rast.filename,
    ST_Value(rast.rast, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
FROM <<TABLE_NAME>> AS rast
WHERE ST_Intersects(ST_SetSRID(ST_MakePoint(%s, %s), 4326), rast.rast)
AND rast.filename IN %s;
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
        ",\n".join(lines)
    ).replace(
        "<<TABLE_NAME>>",
        conf.TABLE
    )

    return sql, values


def get_value_at_points(points, tifs=None):
    """Get the value at the points for the tifs"""
    tifs = tifs or []

    sql = POINT_QUERY_SQL.replace(
        "<<TABLE_NAME>>",
        conf.TABLE
    )

    try:
        conn, cur = get_conn_cur()
        rows = []
        # lazily, for now...
        for lon, lat in points:
            cur.execute(sql, (lon, lat, lon, lat, lon, lat, tifs))
            rows.extend(cur.fetchall())
    finally:
        conn.close()
    return rows


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
        and_stmt = "AND rast.filename IN %s"
        values.append(tifs)

    sql = BUFFER_QUERY_SQL.replace(
        "<<AND_STATEMENTS>>",
        and_stmt
    ).replace(
        "<<TABLE_NAME>>",
        conf.TABLE
    )
    stmts.append(sql)

    try:
        conn, cur = get_conn_cur()
        cur.execute(";\n".join(stmts), values)
        result = cur.fetchall()
    finally:
        conn.close()
    return result
