include:
  - postgresql

dekker-role:
  postgres_user.present:
    - name: {{ pillar['db_role'] }}
    - runas: postgres
    - password: {{ pillar['db_password'] }}
    - superuser: True
    - require:
      - service: postgresql
      - cmd: /var/lib/postgresql/configure_utf-8.sh

postgresql-db:
  postgres_database.present:
    - name: {{ pillar['db_name'] }}
    - runas: postgres
    - encoding: UTF8
    - lc_ctype: en_GB.UTF-8
    - lc_collate: en_GB.UTF-8
    - owner: {{ pillar['db_role'] }}
    - require:
      - postgres_user: dekker-role
