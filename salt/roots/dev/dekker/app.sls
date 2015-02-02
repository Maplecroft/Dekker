dekker source:
  file.symlink:
    - name: {{ pillar['dekker_source_dir'] }}
    - target: /vagrant/app
    - makedirs: True