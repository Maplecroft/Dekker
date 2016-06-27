postgresql:
  pkg:
    - name: postgresql-9.3
    - installed
  service.running:
    - enable: True
    - watch:
      - file: /etc/postgresql/9.3/main/pg_hba.conf

pg_hba.conf:
  file.managed:
     - name: /etc/postgresql/9.3/main/pg_hba.conf
     - source: salt://postgresql/pg_hba.conf
     - template: jinja
     - user: postgres
     - group: postgres
     - mode: 644
     - require:
       - pkg: postgresql-9.3

/var/lib/postgresql/configure_utf-8.sh:
  cmd.run:
    - name: bash /var/lib/postgresql/configure_utf-8.sh
    - user: postgres
    - cwd: /var/lib/postgresql
    - require:
      - pkg: postgresql
      - file: /var/lib/postgresql/configure_utf-8.sh

  file.managed:
     - name: /var/lib/postgresql/configure_utf-8.sh
     - source: salt://postgresql/configure-locale.sh
     - user: postgres
     - group: postgres
     - mode: 755

postgres-pkgs:
  pkg:
    - installed
    - names:
      - postgresql-contrib-9.3