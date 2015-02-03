include:
  - user.group

{{ pillar['user'] }}:
  user.present:
    - home: /home/{{ pillar['user'] }}
    - groups:
      - supervisor
    {% if pillar.get('uid', '') and pillar.get('gid', '') %}
    - uid: {{ pillar['uid'] }}
    - gid: {{ pillar['gid'] }}
    {% endif %}