#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import conf
import os
import psycopg2
import rasterio

from shapely import wkt
from shapely.geometry import Point
from winston.stats import summary


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


def table_exists(table):
    connection, cur = get_conn_cur()
    result = False
    try:
        cur.execute("""
            select exists(
                select * from information_schema.tables where table_name=%s
            )""", (table,)
        )
        result = cur.fetchone()[0]
    finally:
        connection.close()
    return result


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


# Point scoring lookup - get a score for a point
# against a given raster
POINT_QUERY_SQL = """
SELECT
    %s AS lon,
    %s AS lat,
    rast.filename,
    ST_Value(rast.rast, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
FROM "<<TABLE_NAME>>" AS rast
WHERE ST_Intersects(ST_SetSRID(ST_MakePoint(%s, %s), 4326), rast.rast)
AND rast.filename IN %s;
"""

# Point in polygon check
POINT_IN_POLYGON_SQL = """
SELECT
    <<FIELD>>
FROM "<<TABLE_NAME>>"
WHERE ST_Contains(
    geom,
    ST_GeomFromText('POINT(%s %s)', 4326)
);
"""

# Step 1 of buffer/polygon queries: Create an ID'd point or polygon
# that we can create a buffer area to score from.
SET_BUFFER_GEOM_SQL = """
INSERT INTO points_for_buffer(id, geom_or_poly)
    VALUES(%%s, ST_GeomFromText('%s', 4326));
"""

# Step 2.1: Polygon queries: Create a buffer using
# The polygon as it is.
SET_BUFFER_AT_POLYGON_SQL = SET_BUFFER_GEOM_SQL + """
INSERT INTO buffers_for_raster(id, geom)
    SELECT id, geom_or_poly FROM points_for_buffer
    WHERE id = %%s;
"""

# Step 2.2 Point queries - create a buffer around a point expressed
# using metres from geography
SET_BUFFER_AT_POINT_SQL = SET_BUFFER_GEOM_SQL + """
INSERT INTO buffers_for_raster(id, geom)
    SELECT id, ST_Buffer(
        CAST(ST_SetSRID(geom_or_poly, 4326) as geography), %%s
    )::geometry FROM points_for_buffer
    WHERE id = %%s;
"""

# Step 3 of buffer/polygon point scoring.  Actually calculate
# the score using st_clip and st_summarystats.  Please note,
# when rasters are inserted they are broken into pixel chunks/segments
# of the size specified to the raster2pgsql command. i.e.
# this query will operate on lots of mini-rasters not one big
# raster image.
#
# Breakdown of this query:
# 1. create stats_table - this is the st_stats and point id for
#    the buffer area(s) to be scored.  There will be one row
#    in this table for each raster segment (i.e. more than one where
#    our area crosses boundaries between segments)
#
#    1.1  Find the bits of raster that intersects our geometry
#    1.2  ST_Clip the bit of raster to the geometry
#    1.3  Get stats from this clipped bit
#
# 2. Calculated a weighted average of valid scores across segments
#    using the weight defined by the number of pixels within each segment
#
# 3. Done.
#
BUFFER_QUERY_SQL = """
SELECT id, CAST(
        (
            SUM((stats).mean * (stats).count) / SUM((stats).count)
        ) AS decimal(9, 3)) as avgimr FROM (
        SELECT b.id as id,
               (
                    ST_SummaryStats(
                        ST_Clip("<<TABLE_NAME>>".rast, 1, b.geom, true)
                    )
               ) AS stats
         FROM "<<TABLE_NAME>>", buffers_for_raster b
        WHERE b.id IN (%s)
          AND ST_Intersects(b.geom, "<<TABLE_NAME>>".rast)
        ORDER BY b.id
) AS stats_table
GROUP BY id;
"""

# Cleanup query - deletes the buffers from dekker that
# where added using hte above 3 queries to prevent
# re-usage if queried with the same ID
DELETE_BUFFER_AT_GEOM_SQL = """
DELETE FROM points_for_buffer
      WHERE id=%s;

DELETE FROM buffers_for_raster
      WHERE id=%s;
"""


# Per step 2.2 Bufered point queries: buffers on points expressed
# as degrees is not really an exact means.  We use postgis to set
# a buffer on a bit of geography now.
LEGACY_SET_BUFFER_AT_POINT_SQL = SET_BUFFER_GEOM_SQL + """
INSERT INTO buffers_for_raster(id, geom)
    SELECT id, ST_Buffer(geom_or_poly, %%s) FROM points_for_buffer
    WHERE id = %%s;
"""

# Per Step 3 above - ST_Intersection is not a good way of doing this
# though - should use ST_clip but we started with this.  Preserverd
# here as a legacy method for older tools where we need to preserve
# methodology. Should be retired once all tools are killed off or
# are re-scored using the newer methodology.  jpeel - June 2016
LEGACY_BUFFER_QUERY_SQL = """
SELECT id, CAST(AVG(((foo.geomval).val)) AS decimal(9,3)) as avgimr
FROM (
    SELECT b.id, ST_Intersection("<<TABLE_NAME>>".rast, b.geom) AS geomval
    FROM "<<TABLE_NAME>>", buffers_for_raster b
    WHERE ST_Intersects(b.geom, "<<TABLE_NAME>>".rast)
) AS foo
WHERE id = %s
GROUP BY id
ORDER BY id;
"""


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
def set_buffer_at_point(conn, cur, point, buf=25, legacy=False):
    """ Creates a buffer geometry instance for the given point"""

    # point is (lng, lat, id)
    lat = float(point[1])
    lng = float(point[0])
    id = point[2]

    conn.autocommit = True

    # Delete existing buffer
    cur.execute(DELETE_BUFFER_AT_GEOM_SQL, (id, id))

    # Support legacy buffer setting using hard coded km -> degree calculation
    # Bit of an odd one - for at least our test rasters, the 'legacy' path
    # gets an identical result to that retrieved when using the below 'else'
    # block below. If this is true for all rasters, the legacy block can be
    # killed off.
    # i.e. if using legacy st_intersection calculation method, these blocks
    # seem equitiable

    # The same is NOT true for the reverse.  If using the Correct(TM) way of
    # calculating buffer scores with ST_Clip, the old Good Enough(TM) conversion
    # seems to skew the result, at least on our test raster
    # i.e. if using newer st_clip calculation method, these blocks are not equal
    if legacy:
        # Convert from kms to metres. Not perfect, but Good Enough(TM).
        buf = buf / 111.13

        # Set our geometry to a be a single point
        query_string = LEGACY_SET_BUFFER_AT_POINT_SQL % "POINT(%s %s)"
    else:
        # Set buffer using geography and metres radius using the
        # Correct(TM) approach
        buf = buf * 1000

        # Set our geometry to a be a single point
        query_string = SET_BUFFER_AT_POINT_SQL % "POINT(%s %s)"
    # Create the buffer
    cur.execute(query_string, (id, lng, lat, buf, id))


@with_connection
def set_buffer_at_polygon(conn, cur, point_id, polygon):
    """Creates a buffer geometry instance for the given polygon"""
    conn.autocommit = True

    # Delete existing buffer
    cur.execute(DELETE_BUFFER_AT_GEOM_SQL, (point_id, point_id))

    # Set our query type to geometry/geography as needed
    query_string = SET_BUFFER_AT_POLYGON_SQL

    # Set our geometry to a be a polygon point
    query_string = query_string % polygon

    # Create the buffer
    cur.execute(query_string, (point_id, point_id))


@with_connection
def get_buffer_value_at_polygon(conn, cur, point_id, polygon, raster,
                                explain=False):
    if table_exists(raster):
        # Create our buffer
        set_buffer_at_polygon(point_id, polygon)

        # Run the query
        sql = BUFFER_QUERY_SQL.replace("<<TABLE_NAME>>", raster)
        explanation = False
        cur.execute(sql, (point_id,))

        if explain:
            explanation = cur.mogrify(sql, (point_id,))

        return cur.fetchall(), explanation
    else:
        geom = wkt.loads(polygon)
        fname = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'data',
            '{}.tif'.format(raster.rstrip('_raster')),
        )
        with rasterio.open(fname) as src:
            result = summary(src, geom, bounds=(0, 10))
            return [
                (point_id, result.mean),
            ], str(result) if explain else None


@with_connection
def get_buffer_values_at_points(conn, cur, buf, points, raster, explain=False,
                                legacy=False):
    """Get a buffer of approx bufKM around point (lon, lat) in raster."""

    if table_exists(raster):
        # Create buffers
        for point in points:
            set_buffer_at_point(point, buf, legacy=legacy)

        # Create query
        sql = BUFFER_QUERY_SQL.replace("<<TABLE_NAME>>", raster)
        ids = [str(pt[2]) for pt in points]

        # Support legacy ST_intersection scoring
        if legacy:
            sql = LEGACY_BUFFER_QUERY_SQL.replace("<<TABLE_NAME>>", raster)
            explanation = False
            id = point[2]
            cur.execute(sql, (id,))
        else:
            # Otherwise revert to the proper way of doing it
            sql = sql % ", ".join(ids)
            cur.execute(sql)

        # Add explanation?
        explanation = []
        if explain:
            explanation = cur.mogrify(sql)

        # Return results
        result = cur.fetchall()
        return result, explanation
    else:
        fname = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'data',
            '{}.tif'.format(raster.rstrip('_raster')),
        )
        with rasterio.open(fname) as src:
            results = []
            for lon, lat, point_id in points:
                result = summary(
                    src, Point(lat, lon).buffer(buf / 111.13), bounds=(0, 10),
                )
                results.append([(point_id, result.mean)])
            return results, None
