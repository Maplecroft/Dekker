dev:
  '*':
    - source
    - database
    - role
    - environment
    - requirements
    - user
    - virtualenv
    - gunicorn

prod:
  '*':
    - source
    - database
    - role
    - environment
    - requirements
    - user
    - virtualenv
    - gunicorn
