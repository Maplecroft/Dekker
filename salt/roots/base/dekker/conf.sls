{{ pillar['dekker_source_dir'] }}/app/conf.py:
  file.managed:
    - source: salt://dekker/conf-example.py
    - template: jinja
    - user: {{ pillar['user'] }}
    - group: {{ pillar['user'] }}