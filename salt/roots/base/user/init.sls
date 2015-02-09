include:
  - user.group

{{ pillar['user'] }}:
  user.present:
    - home: /home/{{ pillar['user'] }}
    {% if pillar.get('password', '') %}
    - password: {{ pillar['password'] }}
    {% endif %}
    - groups:
      - supervisor
    {% if pillar.get('uid', '') and pillar.get('gid', '') %}
    - uid: {{ pillar['uid'] }}
    - gid: {{ pillar['gid'] }}
    {% endif %}