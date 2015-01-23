/opt/envs/dekker:
  virtualenv.managed:
    - no_site_packages: True
    - cwd: /opt/envs/dekker
    - require:
      - pkg: python-pkgs

dekker-reqs:
  pip.installed:
    - pip_exists_action: switch
    - requirements: /mnt/bootstrap/requirements.txt
    - find_links: http://sw-srv.maplecroft.com/deployment_libs
    - cwd: /opt/envs/dekker
    - pip_bin: /opt/envs/dekker/bin/pip
    - bin_env: /opt/envs/dekker
