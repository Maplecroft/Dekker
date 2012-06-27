-- SELECT
--     buf.filename,
--     CAST(AVG(((buf.geomval).val)) AS decimal(9,7)) as avg
-- FROM (
--     SELECT
--         rast.filename,
--         ST_Intersection(
-- 	    rast.rast,
-- 	    ST_SetSRID(
-- 	        ST_GeomFromEWKT('SRID=4326;POLYGON((-2 51, -2 52, -1 52, -1 51, -2 51))'),
-- 	        4326
-- 	    )
-- 	) AS geomval
--     FROM rasters rast
--     WHERE ST_Intersects(
-- 	ST_SetSRID(
-- 		ST_GeomFromEWKT('SRID=4326;POLYGON((-2 51, -2 52, -1 52, -1 51, -2 51))'), 4326), rast.rast)
--     AND rast.filename = 'SOMERASTER.tif'
-- ) AS buf
-- WHERE (buf.geomval).val >= 0
-- GROUP BY filename
-- ORDER BY filename;


-- SELECT SUM(ST_Area((gv).geom)*(gv).val)/SUM(ST_Area((gv).geom)) AS avg
-- FROM (
-- SELECT ST_Intersection(r.rast,1, p.geom) As gv
-- FROM (SELECT ST_GeomFromEWKT('SRID=4326;POLYGON((-2 51, -2 52, -1 52, -1 51, -2 51))') AS geom) As p INNER JOIN rasters As r
-- ON ST_Intersects(p.geom, r.rast)
-- WHERE r.filename = 'SOMERASTER.tif') As foo;

DROP TABLE IF EXISTS tmp_points;
CREATE TEMP TABLE tmp_points ("gid" int, "point" geometry);
INSERT INTO tmp_points ("gid", "point") VALUES
(100231, ST_MakePoint(172.3, -43.76667)),
(100233, ST_MakePoint(171.71667, -43.91667)),	
(100246, ST_MakePoint(170.92009, -44.09834)),	
(100290, ST_MakePoint(170.95009, -44.44835)),
(100497, ST_MakePoint(173.28271, -42.77409)),	
(100498, ST_MakePoint(171.90983, -43.9236)),
 	(1, ST_MakePoint(-2.136154, 49.220288))	

-- 
-- 	(ST_MakePoint(-4.482422, 39.75788)),
-- 	(ST_MakePoint(-2.482422, 54.75788)),
-- 	(ST_MakePoint(-2, 52)),
-- 	(ST_MakePoint(23.820591, -6.099932)),
-- 	(ST_MakePoint(90.399628, 23.717782)),

;

-- SELECT p.gid, ST_Area((foo.gv).geom) as area, (foo.gv).val as val--SUM(ST_Area((foo.gv).geom)*(foo.gv).val)/SUM(ST_Area((foo.gv).geom)) AS avg
-- FROM (
--   SELECT ST_Intersection(r.rast, 1, ST_SetSRID(p.point, 4326)) AS gv
--   FROM tmp_points AS p
-- 
--   INNER JOIN rasters AS r
--   ON ST_Intersects(ST_SetSRID(p.point, 4326), r.rast)
-- 
--   WHERE r.filename = 'SOMERASTER.tif'
-- ) AS foo, tmp_points p
-- GROUP BY p.gid, area, val
-- ORDER BY p.gid, area, val
-- 
-- ;


-- get the average value arount a point for a given radius
-- 
SELECT
	gid,
	filename,
	lon,
	lat,
	
-- use these two fields and remove group by to see raw vals for averaging
	-- ST_Area((foo.gv).geom),
	-- CAST((foo.gv).val AS decimal(5,3))

-- use this and group by for actual average
	CAST(SUM(ST_Area((foo.gv).geom)*(foo.gv).val)/SUM(ST_Area((foo.gv).geom)) AS decimal(9,7)) as avgimr,
	COUNT(foo.gv) as parts
FROM (
	SELECT

		ST_X(p.point)::NUMERIC(9, 5) AS lon, 
		ST_Y(p.point)::NUMERIC(9, 5) AS lat,
		p.gid,
		sn.filename,
		ST_Intersection(
			--sn.rast,
			ST_Transform(sn.rast, 97099, 'Bilinear'),
			ST_Buffer(ST_Transform(ST_SetSRID(p.point, 4326), 97099), 25000)
		) AS gv
	FROM rasters sn, tmp_points p
	WHERE ST_Intersects(
		ST_Buffer(ST_Transform(ST_SetSRID(p.point, 4326), 97099), 25000),
		--sn.rast
		ST_Transform(sn.rast, 97099, 'Bilinear')
	)
	AND sn.filename = 'SOMERASTER.tif'
) AS foo
WHERE (foo.gv).val >= 0 --AND (foo.gv).val <= 10
GROUP BY filename, gid, lon, lat
ORDER BY filename, gid, lon, lat;


-- get all the diff areas of diff pix values in one tile in which a point lies
-- SELECT ST_Area((ST_DumpAsPolygons(r.rast)).geom),(ST_DumpAsPolygons(r.rast)).val, r.rid from rasters AS r
-- INNER JOIN (SELECT ST_SetSRID(ST_MakePoint(-2, 51), 97099) as pt) AS p
-- ON ST_Intersects(r.rast, p.pt) AND r.filename = 'wsis_2012_97099.tif';


--SELECT * from spatial_ref_sys where srid=97099;
