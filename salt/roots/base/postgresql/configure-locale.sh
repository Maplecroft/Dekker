export LANGUAGE=en_GB.UTF-8
export LANG=en_GB.UTF-8
export LC_ALL=en_GB.UTF-8
pg_dropcluster --stop 9.3 main
pg_createcluster --start -e UTF-8 9.3 main