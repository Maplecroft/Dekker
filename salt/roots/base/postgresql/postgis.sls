include:
  - postgresql.roles

postgis-pkgs:
  pkg.installed:
    - names:
      - postgresql-9.3-postgis-2.1
      - libgdal-dev
    - require:
      - pkg: postgresql

postgis-extension:
  postgres_extension.present:
    - name: postgis
    - maintenance_db: {{ pillar['db_name'] }}
    - requires:
      - postgres_database: postgresql-db
      - pkg: postgis-pkgs

rasters-postgis_topology:
  postgres_extension.present:
    - name: postgis_topology
    - maintenance_db: {{ pillar['db_name'] }}
    - requires:
      - postgres_database: postgresql-db
      - pkg: postgis-pkgs