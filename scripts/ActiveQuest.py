#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ts=2 et
import sys
import os
import re
import json
from QuestInfo import build_quest


def main():
  try:
    (resdir, jsondir) = sys.argv[1:]
  except StandardError:
    sys.stderr.write('Usage: {0} resdir jsondir\n'.format(sys.argv[0]))
    sys.exit(2)

  # クエスト情報を読み込む
  questinfo = build_quest(resdir, 'en')

  # プロファイル情報を読み込む
  with open(os.path.join(jsondir, 'UpdateProfile.req.json'), 'r') as fh:
    active = json.load(fh)['parameters'][1]['activeQuests'].get('quest_id', [])

  goals = []

  for qid in active:
#  for qid in sorted(questinfo.keys()):
    q = questinfo[qid]

    qtype = q['quest']['type']

    if qtype == 'addWish':
      goals.append((
        unicode(qid),
        qtype,
        u'',
        u'',
        u'Wishlist',
        u'x{0}'.format(q['quest']['addWish']['count'])))

    elif qtype == "buyItem":
      goals.append((
        unicode(qid),
        qtype,
        q['itemname'],
        unicode(q['quest']['buyItem']),
        u'',
        u''))

    elif qtype == "collectibles":
      goals.append((
        unicode(qid),
        qtype,
        u'',
        u'',
        u'Any Picture',
        u'x{0}'.format(q['quest']['reward']['money'])))

    elif qtype == "g5invest":
      goals.append((
        unicode(qid),
        qtype,
        q['text']['HINT'],
        u'',
        u'',
        u''))

    elif qtype == "increaseSceneLevel":
      goals.append((
        unicode(qid),
        qtype,
        u'',
        u'',
        q['levelup'][0]['name'],
        q['levelup'][0]['level']))

    elif qtype == "phenomenBanish":
      goals.append((
        unicode(qid),
        qtype,
        u'',
        u'',
        q['phenomen'][0].get('scene', u'ANY'),
        u'{0} x{1}'.format(q['phenomen'][0].get('name', u'ANY'), q['phenomen'][0]['count'])
      ))

    elif qtype == "playMiniGames":
      w = []
      m = []
      for g in q['games']:
        w.append(g.get('name', u'ANY'))
        m.append(u'x{0}'.format(g['count']))

      goals.append((
        unicode(qid),
        qtype,
        u'',
        u'',
        u'/'.join(w),
        u'/'.join(m)))

    elif qtype == "playPhotos":
      w = []
      m = []
      for p in q['photos']:
        w.append(p.get('name', u'ANY'))
        m.append(u'{0} x{1}'.format(p.get('mode', u'ANY'), p.get('count', 1)))

      goals.append((
        unicode(qid),
        qtype,
        u'',
        u'',
        u'/'.join(w),
        u'/'.join(m),
      ))

    elif qtype == "social":
      goals.append((
        unicode(qid),
        qtype,
        q['text']['NAME'],
        u'',
        u'',
        u''))

    elif qtype == "useItem":
      goals.append((
        unicode(qid),
        qtype,
        q['itemname'],
        unicode(q['quest']['useItem']),
        u'',
        u''))

    elif qtype == "findItem":
      for i in q['items']:
        if q['quest'].get('collection'):
          where = u'Combine'
        else:
          where = u'/'.join(i.get('where', []))

        try:
          goals.append((
            unicode(qid),
            qtype,
            i['name'],
            unicode(i['itemid']),
            where,
            u'/'.join(i.get('mode', []))
          ))
        except:
          print json.dumps(i, indent=2)
          raise
          

    else:
      print json.dumps(q, indent=2)
      raise RuntimeError('unknown quest type')

  print u'\t'.join(['Quest', 'Type', 'Goal', 'ItemID', 'Where', 'Mode'])

  for l in goals:
    print u'\t'.join(l).replace(u'"', u'').encode('utf-8')



if __name__ == '__main__':
  main()
