include:
  - postgresql

dekker-role:
  postgres_user.present:
    - name: {{ pillar['user'] }}
    - runas: postgres
    - password: somesecretpassword
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
    - owner: {{ pillar['user'] }}
    - require:
      - postgres_user: dekker-role
