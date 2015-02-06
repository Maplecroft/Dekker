include:
  - supervisord

nginx:
  pkg:
    - installed
  service.running:
    - enable: True
    - restart: True
    - watch:
      - file: /etc/nginx/sites-enabled/dekker.conf
      - file: /etc/nginx/sites-enabled/default
      - pkg: nginx

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
    - template: jinja
    - require:
      - pkg: nginx