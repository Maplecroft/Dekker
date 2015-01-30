include:
  - postgresql.roles

postgis-pkgs:
  pkg.installed:
    - names:
      - postgresql-9.3-postgis-2.1
      - libgdal-dev
    - require:
      - pkg: postgresql

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