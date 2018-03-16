# Create database and user
#sudo apt-get install postgis
sudo -u postgres createuser $USER;
sudo -u postgres dropdb testrasters;
sudo -u postgres createdb testrasters;
sudo -u postgres psql testrasters -c "CREATE EXTENSION postgis";

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Load schema taken from dekker
psql -f $DIR/data/schema.sql testrasters;

# Copy test settings
cp $DIR/test-conf.py $DIR/../app/conf.py

# Load test rasters
raster2pgsql -d -s 4326 -C -I -M $DIR/data/test_raster.tif -F -t 128x128 -N -340282000000000000000000000000000000000 public.dbv_test_raster | psql -d testrasters;

raster2pgsql -d -s 4326 -C -I -M $DIR/data/nh_drought_hazard_2016.tif -F -t 128x128 -N -340282000000000000000000000000000000000 public.dbv_nh_drought_hazard_2016_raster | psql -d testrasters
raster2pgsql -d -s 4326 -C -I -M $DIR/data/nh_extra_tropical_cyclone_hazard_2016.tif -F -t 128x128 -N -340282000000000000000000000000000000000 public.dbv_nh_extra_tropical_cyclone_hazard_2016_raster | psql -d testrasters
raster2pgsql -d -s 4326 -C -I -M $DIR/data/nh_flood_hazard_2016.tif -F -t 128x128 -N -340282000000000000000000000000000000000 public.dbv_nh_flood_hazard_2016_raster | psql -d testrasters
raster2pgsql -d -s 4326 -C -I -M $DIR/data/nh_landslide_earthquake_related_hazard_2016.tif -F -t 128x128 -N -340282000000000000000000000000000000000 public.dbv_nh_landslide_earthquake_related_hazard_2016_raster | psql -d testrasters
raster2pgsql -d -s 4326 -C -I -M $DIR/data/nh_natural_hazards_economic_exposure_absolute_2016.tif -F -t 128x128 -N -340282000000000000000000000000000000000 public.dbv_nh_natural_hazards_population_exposure_abs_2016_raster | psql -d testrasters
raster2pgsql -d -s 4326 -C -I -M $DIR/data/nh_seismic_hazard_2016.tif -F -t 128x128 -N -340282000000000000000000000000000000000 public.dbv_nh_seismic_hazard_2016_raster | psql -d testrasters
raster2pgsql -d -s 4326 -C -I -M $DIR/data/nh_wildfire_hazard_2016.tif -F -t 128x128 -N -340282000000000000000000000000000000000 public.dbv_nh_wildfire_hazard_2016_raster | psql -d testrasters
raster2pgsql -d -s 4326 -C -I -M $DIR/data/cc_total_ghg_emissions_2016.tif -F -t 32x32 -N -340282000000000000000000000000000000000 public.dbv_cc_total_ghg_emissions_2016_raster | psql -d testrasters;
raster2pgsql -d -s 4326 -C -I -M $DIR/data/cc_climate_model_uncertainty_2016.tif -F -t 128x128 -N -340282000000000000000000000000000000000 public.dbv_cc_climate_model_uncertainty_2016_raster | psql -d testrasters;
raster2pgsql -d -s 4326 -C -I -M $DIR/data/cc_air_quality_2016.tif -F -t 32x32 -N -340282000000000000000000000000000000000 public.dbv_cc_air_quality_2016_raster | psql -d testrasters

