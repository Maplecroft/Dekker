nginx:
  pkg:
    - installed
  service:
    - running

# Remove default nginx site
/etc/nginx/sites-enabled/default:
  file.absent: []

/etc/nginx/sites-enabled:
  file.directory:
    - require:
        - pkg: nginx

/etc/nginx/sites-enabled/dekker.conf:
  file.symlink:
    - target: /etc/nginx/sites-available/dekker.conf
    - watch:
        - file: /etc/nginx/sites-enabled
        - file: /etc/nginx/sites-available/dekker.conf

/etc/nginx/sites-available/dekker.conf:
  file.managed:
    - source: salt://nginx/dekker.conf
    - require:
      - pkg: nginx

service nginx reload:
  cmd.run:
    - watch:
      - file: /etc/nginx/sites-enabled/dekker.conf
      - file: /etc/nginx/sites-enabled/default
