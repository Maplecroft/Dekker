python2:
  pkg:
    - installed
    - name: python

python-pkgs:
  pkg:
    - installed
    - names:
      - python-pip
      - python-dev
      - python-virtualenv
      - build-essential
    - require:
      - pkg: python2
