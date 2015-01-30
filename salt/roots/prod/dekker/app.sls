dekker source:
  - require:
    - name: {{ pillar['dekker_source_dir'] }}
    - file.exists: /