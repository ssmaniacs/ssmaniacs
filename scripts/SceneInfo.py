#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ts=2 et

import sys
import os
import json
import urllib2
from xml.etree import ElementTree

SELF_UID = 'suid_20699361'

def http_post(body, proxy):
  headers = {
    'Host': 'sh.g5e.com',
    'X-mytona-fix': '1',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Content-Length': '{0}'.format(len(body)),
    'Accept-Encoding': 'identity, gzip',
  }

  req = urllib2.Request(
    url='http://sh.g5e.com/hog_ios/jsonway_android.php',
    data=body, headers=headers)

  if proxy:
    req.set_proxy(proxy, 'http')

  fh = urllib2.urlopen(req, timeout=30.0)

  res = fh.read()

  return json.loads(res)


def get_profile():
  body = {
    "serviceName": "GameService",
    "methodName": "GetProfiles",
    "parameters": [
      [ SELF_UID ],
      None,
      53
    ]
  }

  return http_post(json.dumps(body, indent=2), None)


def main():
  try:
    resdir = sys.argv[1]
  except StandardError:
    sys.stderr.write('Usage: {0} resdir\n'.format(sys.argv[0]))
    sys.exit(2)

  scenes = {}
  level_name = {}
  phenom_name = {}
  scene_type = {}

  # Load scenes names and level names
  with open(os.path.join(resdir, '1024', 'properties', 'default.xml'), 'r') as fh:
    for line in fh:
      try:
        if line.startswith('IDS_SCENE_NAME_'):
          key, val = line.split(':', 1)
          id_ = int(key.rsplit('_', 1)[-1])
          scenes[id_] = {'name': val.strip().strip('"')}

        elif line.startswith('IDS_SCENE_STAGE_'):
          key, val = line.split(':', 1)
          id_ = int(key.rsplit('_', 1)[-1])
          level_name[id_] = val.strip()

        elif line.startswith('IDS_PHENOMEN_'):
          key, val = line.split(':', 1)
          id_ = int(key.rsplit('_', 1)[-1])
          phenom_name[id_] = val.strip()

        elif line.startswith('IDS_SCENE_TYPE_'):
          key, val = line.split(':', 1)
          id_ = int(key.rsplit('_', 1)[-1])
          scene_type[id_] = val.strip()

      except ValueError:
        pass

  # Load scenes parameters
  with open(os.path.join(resdir, '1024', 'properties', 'data_scenes.xml'), 'r') as fh:
    tree = ElementTree.parse(fh)

  for s in tree.findall('scene'):
    id_ = int(s.get('id'))
    scenes[id_]['levels'] = []

    for l in s.findall('level'):
      p = l.find('params')
      scenes[id_]['levels'].append({
        'energy': int(p.get('energy')),
        'nextlv': int(p.get('progress'))
      })

  # Load progress profiles
  profile = get_profile()
  param = profile['response'][0]['data']

  # match profiles
  for (id_, val) in zip(param['scenelevel']['scene_id'], param['scenelevel']['level']):
    if id_ in scenes:
      scenes[id_]['level'] = val

  for (id_, val) in zip(param['sceneprogress']['scene_id'], param['sceneprogress']['progress']):
    if id_ in scenes:
      scenes[id_]['progress'] = val

  for (id_, val) in zip(param['scenetypes']['scene_id'], param['scenetypes']['type']):
    if id_ in scenes:
      scenes[id_]['mode'] = scene_type[val]

  for (id_, val) in zip(param['scenephenomens']['scene_id'], param['scenephenomens']['type']):
    if id_ in scenes:
      scenes[id_]['phenom'] = phenom_name[val]

  for (id_, info) in sorted(scenes.items()):
    if 'progress' not in info:
      continue

    progress = float(info['progress'] * 100) / info['levels'][info['level']]['nextlv']

    print ','.join([
      str(id_),
      info['name'],
      level_name[info['level']],
      str(progress),
      info.get('phenom', info['mode']),
    ] + [str(l['energy']) for l in info['levels']])


if __name__ == '__main__':
  main()
