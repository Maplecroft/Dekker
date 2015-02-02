{{ pillar['user'] }}:
  user.present:
    - home: /home/{{ pillar['user'] }}
    {% if pillar.get('uid', '') and pillar.get('gid', '') %}
    - uid: {{ pillar['uid'] }}
    - gid: {{ pillar['gid'] }}
    {% endif %}