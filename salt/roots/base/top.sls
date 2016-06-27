dev:
  '*':
    - user
    - postgresql.postgis
    - dekker
    - python
    - supervisord
    - nginx
    - gunicorn

prod:
  '*':
    - user
    - postgresql.postgis
    - dekker
    - python
    - supervisord
    - nginx
    - gunicorn