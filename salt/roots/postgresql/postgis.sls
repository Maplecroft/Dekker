include:
  - postgresql

postgis-pkgs:
  pkg.installed:
    - names:
      - postgresql-9.3-postgis-2.1
      - libgdal-dev
    - require:
      - pkg: postgresql

rasters-user:
  postgres_user.present:
    - name: rasters
    - runas: postgres
    - superuser: True
    - require:
      - service: postgresql
      - cmd: /var/lib/postgresql/configure_utf-8.sh

tiles-user:
  postgres_user.present:
    - name: tiles
    - runas: postgres
    - superuser: True
    - require:
      - service: postgresql
      - cmd: /var/lib/postgresql/configure_utf-8.sh

rasters-db:
  postgres_database.present:
    - name: rasters
    - runas: postgres
    - encoding: UTF8
    - lc_ctype: en_GB.UTF-8
    - lc_collate: en_GB.UTF-8
    - owner: tiles
    - require:
      - postgres_user: rasters-user
      - postgres_user: tiles-user

rasters-postgis:
  postgres_extension.present:
    - name: postgis
    - maintainance_db: rasters
    - user: postgres
    - requires:
      - postgres_database: rasters-db
      - pkg: postgis-pkgs

rasters-postgis_topology:
  postgres_extension.present:
    - name: postgis_topology
    - maintainance_db: rasters
    - user: postgres
    - requires:
      - postgres_database: rasters-db
      - pkg: postgis-pkgs