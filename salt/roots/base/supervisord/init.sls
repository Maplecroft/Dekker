/etc/supervisor/supervisord.conf:
  file.managed:
    - source: salt://supervisord/supervisord.conf
    - makedirs: True
    - template: jinja

/etc/supervisor/conf.d/dekker.conf:
  file.managed:
    - source: salt://supervisord/dekker.conf
    - makedirs: True
    - template: jinja

supervisor:
  pkg:
    - installed