include:
  - postgresql

rasters-role:
  postgres_user.present:
    - name: rasters
    - runas: postgres
    - superuser: True
    - require:
      - service: postgresql
      - cmd: /var/lib/postgresql/configure_utf-8.sh

tiles-role:
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
      - postgres_user: rasters-role
      - postgres_user: tiles-role