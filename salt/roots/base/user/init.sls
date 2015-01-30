{{ pillar['user'] }}:
  user.present:
    - shell: /bin/zsh
    - home: /home/{{ pillar['user'] }}
    - uid: 1000
    - gid: 1000