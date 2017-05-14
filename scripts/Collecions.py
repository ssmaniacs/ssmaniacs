#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ts=2 et
import sys
import os
import re
import json

from TextInfo import load_textinfo
from QuestInfo import build_quest


def main():
  try:
    (resdir, jsondir, lang) = sys.argv[1:]
  except StandardError:
    sys.stderr.write('Usage: {0} resdir jsondir lang\n'.format(sys.argv[0]))
    sys.exit(2)

  quests = build_quest(resdir, lang)
  items = {}

  for q in quests.values():
    for i in q.get('items', []):
      items[i['itemid']] = q['quest']['uid']
 
  textinfo = load_textinfo(resdir, lang)

  with open(os.path.join(resdir, '1024', 'properties', 'collections.json'), 'r') as fh:
    coldata = json.load(fh)

  with open(os.path.join(jsondir, 'UpdateProfile.req.json'), 'r') as fh:
    jdata = json.load(fh)
    done = jdata['parameters'][1]['LoggedQuests']
    active = jdata['parameters'][1]['activeQuests'].get('quest_id', [])

  line = []
  for i in range(1, 7):
    line.append('name{0}'.format(i))
    line.append('id{0}'.format(i))
    line.append('quest{0}'.format(i))
    line.append('stat{0}'.format(i))

  print '\t'.join(line)

  for c in coldata:
    if c['type'] != 'collection':
      continue

    line = []
    for i in c['items'] + [c['main_item_id']]:
      name = textinfo['ITEM'][i]['NAME']
      if not isinstance(name, basestring):
        name = name[-1]

      qid = items.get(i, -1)

      if qid in active:
        status = u'A'
      elif qid in done:
        status = u'D'
      else:
        status = u''

      line.append(name)
      line.append(unicode(i))
      line.append(unicode(qid))
      line.append(status)

    print u'\t'.join(line).encode('utf-8')


if __name__ == '__main__':
  main()
