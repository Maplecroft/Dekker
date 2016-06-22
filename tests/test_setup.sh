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

