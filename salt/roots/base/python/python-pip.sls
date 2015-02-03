dekker-virtualenv:
  virtualenv.managed:
    - name: {{ pillar['virtualenv'] }}
    - no_site_packages: True
    - cwd: {{ pillar['virtualenv'] }}
    - user: {{ pillar['user'] }}
    - require:
      - user: {{ pillar['user'] }}
      - pkg: python-pkgs

dekker-reqs-file:
  file.exists:
    - name: {{ pillar['requirements_dir'] }}/{{ pillar['requirements_file'] }}.txt

dekker-reqs:
  pip.installed:
    - pip_exists_action: switch
    - requirements: {{ pillar['requirements_dir'] }}/{{ pillar['requirements_file'] }}.txt
    - find_links: http://sw-srv.maplecroft.com/deployment_libs
    - cwd: {{ pillar['virtualenv'] }}
    - pip_bin: {{ pillar['virtualenv'] }}/bin/pip
    - bin_env: {{ pillar['virtualenv'] }}
    - requires:
      - file: {{ pillar['dekker_source_dir'] }}
      - file: dekker-reqs-file
