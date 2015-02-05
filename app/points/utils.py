#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
import psycopg2

from app import conf


TEMP_TABLE_SQL = """
DROP TABLE IF EXISTS tmp_points;
CREATE TEMP TABLE tmp_points ("gid" int, "point" geometry);
INSERT INTO tmp_points ("gid", "point") VALUES
    <<VALUES_STATEMENTS>>
"""


BUFFER_QUERY_SQL_201 = """
SELECT
    gid, filename, lon, lat,
    CAST(
        SUM(
            ST_Area((foo.gv).geom) * (foo.gv).val
        ) / SUM(ST_Area((foo.gv).geom)) AS decimal(9,7)) as avgimr,
    COUNT(foo.gv) as parts
FROM (
    SELECT

        ST_X(p.point)::NUMERIC(9, 5) AS lon,
        ST_Y(p.point)::NUMERIC(9, 5) AS lat,
        p.gid,
        sn.filename,
        ST_Intersection(
            ST_Transform(sn.rast, 97099, 'Bilinear'),
            ST_Buffer(ST_Transform(ST_SetSPATIAL_REFERENCE_ID(p.point, %s), 97099), %s)
        ) AS gv
    FROM <<TABLE_NAME>> sn, tmp_points p
    WHERE ST_Intersects(
        ST_Buffer(ST_Transform(ST_SetSPATIAL_REFERENCE_ID(p.point, %s), 97099), %s),
        ST_Transform(sn.rast, 97099, 'Bilinear')
    )
    <<AND_STATEMENTS>>
) AS foo
WHERE (foo.gv).val >= 0 --AND (foo.gv).val <= 10
GROUP BY filename, gid, lon, lat
ORDER BY filename, gid, lon, lat;
"""


POINT_QUERY_SQL = """
SELECT
    %s AS lon,
    %s AS lat,
    rast.filename,
    ST_Value(rast.rast, ST_SetSPATIAL_REFERENCE_ID(ST_MakePoint(%s, %s), 4326))
FROM <<TABLE_NAME>> AS rast
WHERE ST_Intersects(ST_SetSPATIAL_REFERENCE_ID(ST_MakePoint(%s, %s), 4326), rast.rast)
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
    SELECT id, ST_Buffer(geom, 0.2249) FROM points_for_buffer
    WHERE id = %s;
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


def get_point_in_polygon_value(point, table, field, explain=False):
    """
    Given a lat-lon point and a PostGIS table, get the field value
    of the polygon that contains the point.
    """
    row = ''
    sql = POINT_IN_POLYGON_SQL.replace(
        "<<TABLE_NAME>>", table).replace(
        "<<FIELD>>", field)
    explanation = [] if explain else False
    try:
        conn, cur = get_conn_cur()
        lat = float(point.get('lat'))
        lon = float(point.get('lon'))
        cur.execute(sql, (lon, lat))
        if explain:
            explanation.append(cur.mogrify(sql, (lon, lat)))
        values = cur.fetchall()
        value = values[0][0] if len(values) > 0 else ''
        row = [field, value]
    finally:
        conn.close()
    if explain:
        explanation = "\n".join(explanation)
    return row, explanation


def get_value_at_points(points, tifs=None, explain=False):
    """Get the value at the points for the tifs"""
    tifs = tifs or []

    sql = POINT_QUERY_SQL.replace(
        "<<TABLE_NAME>>",
        conf.TABLE
    )

    explanation = [] if explain else False
    try:
        conn, cur = get_conn_cur()
        rows = []
        # lazily, for now...
        for lon, lat in points:
            cur.execute(sql, (lon, lat, lon, lat, lon, lat, tifs))
            if explain:
                explanation.append(
                    cur.mogrify(sql, (lon, lat, lon, lat, lon, lat, tifs)))
            rows.extend(cur.fetchall())
    finally:
        conn.close()
    if explain:
        explanation = "\n".join(explanation)
    return rows, explanation


def get_buffer_value_at_points(buf, points, tifs=None, explain=False):
    """
    Deprecated, superseded by the more simple and efficient
    `get_buffer_value_at_point`
    """

    tifs = tifs or []

    one_degree = 111.13  # ish, varying about the equator...
    buf_degrees = buf / one_degree

    stmts = []

    test_point = points[0]
    if len(test_point) == 2:  # then it has no ID
        points = [(n, p[0], p[1]) for n, p in enumerate(points)]

    sql, values = get_points_table(points)
    values.extend([conf.SPATIAL_REFERENCE_ID, buf_degrees, conf.SPATIAL_REFERENCE_ID, buf_degrees])
    stmts.append(sql)

    and_stmt = ""
    if len(tifs) > 0:
        and_stmt = "AND sn.filename IN %s"
        values.append(tifs)

    sql = BUFFER_QUERY_SQL_201.replace(
        "<<AND_STATEMENTS>>",
        and_stmt
    ).replace(
        "<<TABLE_NAME>>",
        conf.TABLE
    )
    stmts.append(sql)
    explanation = False
    try:
        conn, cur = get_conn_cur()
        cur.execute(";\n".join(stmts), values)
        if explain:
            explanation = cur.mogrify(";\n".join(stmts), values)
        result = cur.fetchall()
    finally:
        conn.close()
    return result, explanation


def set_buffer_at_point(point):
    """
    Checks if a buffer geometry exists for the current point and if not
    it creates it.
    """
    # point is (lng, lat, id)
    lat = float(point[1])
    lng = float(point[0])
    id = point[2]
    try:
        conn, cur = get_conn_cur()
        conn.autocommit = True
        cur.execute(GET_BUFFER_AT_POINT, (id,))
        values = cur.fetchall()
        if len(values) == 0:
            # Create the buffer
            cur.execute(SET_BUFFER_AT_POINT_SQL, (id, lat, lng, lng, lat, id))
    finally:
        conn.close()


def get_buffer_value_at_point(buf, point, raster, explain=False):
    """Get a buffer of approx bufKM around point (lon, lat) in raster."""
    # point is (lng, lat, id)
    set_buffer_at_point(point)
    sql = BUFFER_QUERY_SQL.replace("<<TABLE_NAME>>", raster)
    explanation = False
    id = point[2]
    try:
        conn, cur = get_conn_cur()
        cur.execute(sql, (id,))
        if explain:
            explanation = cur.mogrify(sql, (id,))
        result = cur.fetchall()
    finally:
        conn.close()
    return result, explanation
