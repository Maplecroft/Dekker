/var/log/gunicorn:
  file.directory:
    - user: {{ pillar['user'] }}
    - group: {{ pillar['user'] }}
    - mode: 755

{{ pillar['gunicorn_conf'] }}:
  file.managed:
    - source: salt://gunicorn/gunicorn.conf
    - template: jinja
    - user: {{ pillar['user'] }}
    - group: {{ pillar['user'] }}

supervisored-gunicorn:
  supervisord.running:
    - name: dekker
    - user: {{ pillar['user'] }}
    - update: True
    - restart: True
    - require:
      - pkg: supervisor
      - file: /etc/supervisor/supervisord.conf
    - watch:
      - file: {{ pillar['gunicorn_conf'] }}


