/opt/envs/dekker:
  virtualenv.managed:
    - no_site_packages: True
    - cwd: /opt/envs/dekker
    - require:
      - pkg: python-pkgs

requirements-file:
  file.exists:
    - name: /vagrant/requirements/development.txt

dekker-reqs:
  pip.installed:
    - pip_exists_action: switch
    - requirements: /vagrant/requirements/development.txt
    - find_links: http://sw-srv.maplecroft.com/deployment_libs
    - cwd: /opt/envs/dekker
    - pip_bin: /opt/envs/dekker/bin/pip
    - bin_env: /opt/envs/dekker
    - requires:
      - file: requirements-file
