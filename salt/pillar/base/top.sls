dev:
  '*':
    - source
    - environment
    - requirements
    - user
    - virtualenv
    - gunicorn

prod:
  '*':
    - source
    - environment
    - requirements
    - user
    - virtualenv
    - gunicorn
