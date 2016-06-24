# Create database and user
dropdb testrasters;
createuser dekker;
createdb testrasters;

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Load schema taken from dekker
psql -f $DIR/data/dekker_schema.sql testrasters;

# Copy test settings
cp $DIR/test-conf.py $DIR/../conf.py

# Load test raster
raster2pgsql -d -s 4326 -C -I -M $DIR/data/test_raster.tif -F -t 128x128 -N -340282000000000000000000000000000000000 public.test_raster | psql -d testrasters;
# Equivalent: raster2pgsql -d -s 4326 -C -I -M cse16_i -F -t 128x128 -N -340282000000000000000000000000000000000 public.nh_extra_tropical_cyclone_hazard_2016_raster | psql -d rasters


raster2pgsql -d -s 4326 -C -I -M $DIR/data/drg16_i.tif -F -t 128x128 -N -340282000000000000000000000000000000000 public.nh_drought_hazard_2016_raster | psql -d testrasters
raster2pgsql -d -s 4326 -C -I -M $DIR/data/cse16_i.tif -F -t 128x128 -N -340282000000000000000000000000000000000 public.nh_extra_tropical_cyclone_hazard_2016_raster | psql -d testrasters
raster2pgsql -d -s 4326 -C -I -M $DIR/data/fld16_i.tif -F -t 128x128 -N -340282000000000000000000000000000000000 public.nh_flood_hazard_2016_raster | psql -d testrasters
raster2pgsql -d -s 4326 -C -I -M $DIR/data/lse16_i.tif -F -t 128x128 -N -340282000000000000000000000000000000000 public.nh_landslide_earthquake_related_hazard_2016_raster | psql -d testrasters
raster2pgsql -d -s 4326 -C -I -M $DIR/data/ppx16_i.tif -F -t 128x128 -N -340282000000000000000000000000000000000 public.nh_natural_hazards_population_exposure_abs_2016_raster | psql -d testrasters
raster2pgsql -d -s 4326 -C -I -M $DIR/data/ssm16_i.tif -F -t 128x128 -N -340282000000000000000000000000000000000 public.nh_seismic_hazard_2016_raster | psql -d testrasters
raster2pgsql -d -s 4326 -C -I -M $DIR/data/wfr16_i.tif -F -t 128x128 -N -340282000000000000000000000000000000000 public.nh_wildfire_hazard_2016_raster | psql -d testrasters
raster2pgsql -d -s 4326 -C -I -M $DIR/data/ghg16_i.tif -F -t 32x32 -N -340282000000000000000000000000000000000 public.cc_total_ghg_emissions_2016_raster | psql -d testrasters;
raster2pgsql -d -s 4326 -C -I -M $DIR/data/cmu16_i.tif -F -t 128x128 -N -340282000000000000000000000000000000000 public.cc_climate_model_uncertainty_2016_raster | psql -d testrasters;
raster2pgsql -d -s 4326 -C -I -M $DIR/data/aq16_i.tif -F -t 32x32 -N -340282000000000000000000000000000000000 public.cc_air_quality_2016_raster | psql -d testrasters

#CHECK
#raster2pgsql -d -s 4326 -C -I -M $DIR/data/ecx16_i.tif -F -t 128x128 -N -340282000000000000000000000000000000000 public.nh_natural_hazards_economic_exposure_absolute_2016_raster | psql -d testrasters


