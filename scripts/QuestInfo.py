#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ts=2 et
import sys
import os
import json
import re
from TextInfo import load_textinfo


def load_diary(resdir):
  '''load diary-quest depencency file'''
  path = os.path.join(resdir, '1024',
    'properties', 'diary_page_dependency.json')

  with open(path, 'r') as fh:
    jdata = json.load(fh)['dependency']

  diary = {}
  for v in jdata:
    if v['QuestId'] in diary:
      raise RuntimeError(
        'Duplicate QuestId {0} in diary_page_dependency.json'.format(v['QuestId']))

    diary[v['QuestId']] = v['DiaryPage']

  return diary


def load_letters(resdir):
  '''load letter-quest dependency file'''
  path = os.path.join(resdir, '1024', 'properties', 'data_letters.xml')
  with open(path, 'r') as fh:
    # the file is written in JSON, despite the 'xml' extension
    jdata = json.load(fh)['letters']

  letters = {}
  for v in jdata:
    if v.get('questDef', 0) <= 0:
      continue

    if v['questDef'] in letters:
      raise RuntimeError(
        'Duplicate QuestId {0} in data_letters.xml'.format(v['questDef']))

    letters[v['questDef']] = v['identifier']

  return letters


def load_quests(resdir):
  '''load quest info file'''
  path = os.path.join(resdir, '1024', 'properties', 'quests.xml')
  with open(path, 'r') as fh:
    # the file is written in JSON, despite the 'xml' extension
    return json.load(fh)['quests']


MODETYPE = {
  "text": 0,
  "night": 1,
  "siluet": 2,
  "part": 6,
  "morph": 8,
  "couple": 10,
}


def build_quest(resdir, lang):
  textinfo = load_textinfo(resdir, lang)
  diary = load_diary(resdir)
  quests = load_quests(resdir)
  letters = load_letters(resdir)

  qlist = {}

  for src in quests.values():
    try:
      uid = src['uid']
      if uid not in qlist:
        qlist[uid] = {}

      dst = qlist[uid]

      dst['quest'] = src
      dst['text'] = textinfo['QUEST'].get(uid)

      if uid in diary:
        dst['diary'] = textinfo['DIARY'][diary[uid]]

      for key, val in src.items():
        if key == 'avatar':
          dst['avatar'] = textinfo['PERSON'].get(val, {}).get('NAME')

        elif key == 'sceneDependency':
          dst['dependscene'] = [textinfo['SCENE'][i]['NAME'] for i in val]

        elif key == 'letterDependency':
          dst['letters'] = [textinfo['LETTER'][i] for i in val]

        elif key == 'unlockSceneId':
          if val > 0:
            dst['unlockscene'] = textinfo['SCENE'][val]['NAME']

        elif key == 'eventSceneId':
          dst['eventScene'] = textinfo['SCENE'][val]['NAME']

        elif key == 'findItem':
          dst['items'] = []
          for i in val.values():
            item = {}

            for k, v in i.items():
              if k == 'itemId':
                item['itemid'] = v
                item['name'] = textinfo['ITEM'].get(v, {}).get('NAME')

              elif k == 'lookInScenes':
                item['where'] = [textinfo['SCENE'][j]['NAME'] for j in v['sceneId']]

                for k2 in v:
                  if k2 not in ('sceneId', 'chance'):
                    raise RuntimeError('Unknown key ' + k2)

              elif k == 'lookInPuzzle':
                item['where'] = [textinfo['PUZZLE'][j]['NAME'] for j in v['puzzleId']]

                for k2 in v:
                  if k2 not in ('puzzleId', 'chance'):
                    raise RuntimeError('Unknown key ' + k2)

              elif k == 'Chances':
                for k2, v2 in v.items():
                  if k2 == 'scenes':
                    item['where'] = [textinfo['SCENE'][j]['NAME'] for j in v2]
                  elif k2 == 'mode':
                    item['mode'] = [textinfo['SCENETYPE'][MODETYPE[j]]['NAME'] for j in v2]
                  elif k2 == 'anomaly':
                    item['mode'] = [textinfo['PHENOMEN'][j]['NAME'] for j in v2]
                  elif k2 == 'type':
                    if v2 in ('curse', 'curse_scene'):
                      item['mode'] = [textinfo['PHENOMEN'][10]['NAME']]
                  elif k2 not in ('chance', 'type'):
                    raise RuntimeError('Unknown key ' + k2)

              elif k == 'count':
                item['count'] = v

              elif k not in ('count'):
                raise RuntimeError('Unknown key ' + k)

            dst['items'].append(item)

        elif key == 'playMiniGames':
          dst['games'] = []
          for i in val.values():
            item = {}
            for k, v in i.items():
              if k == 'puzzleId':
                if v >= 0:
                  item['name'] = textinfo['PUZZLE'].get(i['puzzleId'],{}).get('NAME')

              elif k == 'count':
                item['count'] = v

              else:
                raise RuntimeError('Unknown key ' + k)

            dst['games'].append(item)

        elif key == 'playPhotos':
          dst['photos'] = []
          for i in val.values():
            item = {}
            for k, v in i.items():
              if k == 'sceneId':
                if v >= 0:
                  item['name'] = textinfo['SCENE'].get(v,{'NAME': 'どこでも'})['NAME']

              elif k == 'type':
                if v >= 0:
                  item['mode'] = textinfo['SCENETYPE'].get(v, {'NAME': 'ANY'})['NAME']

              elif k == 'count':
                item['count'] = v

              elif k not in ('count'):
                raise RuntimeError('Unknown key ' + k)

            dst['photos'].append(item)

        elif key == 'increaseSceneLevel':
          dst['levelup'] = []
          for i in val.values():
            item = {
              'name': textinfo['SCENE'].get(i['sceneId'],{}).get('NAME'),
              'level': textinfo['LEVEL'][i['sceneLevel']]['NAME']
            }
            dst['levelup'].append(item)

        elif key == 'phenomenBanish':
          dst['phenomen'] = []
          for i in val.values():
            item = {
              'count': i['count'],
              'forced': i.get('noEarlyBanish', False)
            }

            if i['phenomenId'] >= 0:
              item['name'] = textinfo['PHENOMEN'][i['phenomenId']]['NAME']

            if i['sceneId'] >= 0:
              item['scene'] = textinfo['SCENE'][i['sceneId']]['NAME']


            dst['phenomen'].append(item)
      
        elif key == 'dependency':
          for dep in val:
            if dep not in qlist:
              qlist[dep] = {}

            if 'depended_by' not in qlist[dep]:
              qlist[dep]['depended_by'] = []

            qlist[dep]['depended_by'].append(uid)

        elif key in ('buyItem', 'useItem'):
          dst['itemname'] = textinfo['ITEM'].get(val, {'NAME': 'itemid:'+str(val)}).get('NAME')

        elif key not in ('reward', 'uid', 'collection', 'accessLevel', 'type', 'event_uid', 'disable', 'event', 'comicsQuest', 'notifyWindow', 'addDef', 'addWish', 'g5invest', 'useItem', 'social', 'buyItem'):
          print 'Unknown key ' + key
          print json.dumps(src, indent=2, ensure_ascii=False).encode('utf-8')
          sys.exit(0)

    except:
      print json.dumps(src, indent=2, ensure_ascii=False).encode('utf-8')
      raise

  return qlist


def print_quest(qinfo):

  DELIM = u'\t'

  print DELIM.join([
    u'クエストID',
    u'発生条件',
    u'次クエスト',
    u'人物',
    u'クエスト名',
    u'クエスト',
    u'ヒント',
    u'クリア',
    u'クエスト種別',
    u'目的',
    u'場所',
    u'報酬',
    u'日記タイトル',
    u'日記内容',
  ]).encode('utf-8')

  for key, val in qinfo.items():
    if val['quest'].get('dependency'):
      continue

    def printinfo(uid, info):
      line = []
      line.append(str(uid))

      # 発生条件
      condition = []
      if 'dependscene' in info:
        for i in  info['dependscene']:
          condition.append(u'{0}アンロック'.format(i))

      if info['quest'].get('accessLevel', 0) > 1:
        condition.append(u'レベル{0}'.format(info['quest']['accessLevel']))

      if 'dependency' in info['quest']:
        for i in sorted(info['quest']['dependency']):
          condition.append(u'クエスト{0}'.format(i))

      line.append(u'\\n'.join(condition))

      # 次クエスト
      if 'depended_by' in info:
        line.append(u','.join([u'{0}'.format(i) for i in sorted(info['depended_by'])]))
      else:
        line.append(u'')

      # アバター
      line.append(info['avatar'])

      # クエストテキスト
      try:
        if info['text']:
          name = info['text'].get('NAME', u'')
          text = info['text'].get('TEXT', u'')
          hint = info['text'].get('HINT', u'')
          win  = info['text'].get('WIN', u'')

          if isinstance(name, list) and not isinstance(name, basestring):
            name = name[-1]

          if isinstance(text, list) and not isinstance(text, basestring):
            text = text[-1]

          if isinstance(hint, list) and not isinstance(hint, basestring):
            hint = hint[-1]

          if isinstance(win , list) and not isinstance(win , basestring):
            win  = win [-1]

        else:
          name = u''
          text = u''
          hint = u''
          win  = u''

        line.append(name)
        line.append(text)
        line.append(hint)
        line.append(win)

      except:
        print info
        raise

      # クエスト種類
      if info['quest']['type'] == 'addWish':
        line.append(u'ウィッシュリスト')
        line.append(u'ウィッシュリストにアイテムを{0}個追加'.format(
          info['quest']['addWish']['count']))
        line.append(u'')

      elif info['quest']['type'] == 'findItem':
        goals = {}
        places = set()
        for i in info['items']:
          goal = u'{0}を入手する'.format(i['name'])
          goals[goal] = goals.get(goal, 0) + 1

          if 'where' in i and 'mode' in i:
            for p,m in zip(i['where'], i['mode']):
              places.add(u'写真:{0} モード:{1}'.format(p, m))

          elif 'where' in i:
            for p in i['where']:
              places.add(u'写真:{0}'.format(p))

          elif 'mode' in i:
            for m in i['mode']:
              places.add(u'モード:{0}'.format(m))

        if info['quest'].get('collection'):
          places = (u'コレクションを組み合わせる',)

        goal2 = []
        for k, v in sorted(goals.items()):
          if v > 1:
            goal2.append(k + u' x{0}'.format(v))
          else:
            goal2.append(k)

        line.append(u'アイテム入手')
        line.append(u'\\n'.join(goal2))
        line.append(u'\\n'.join(places))


      elif info['quest']['type'] == 'playPhotos': 
        goals = set()
        for i in info['photos']:
          goals.add(u'写真:{0} モード:{1} x{2}'.format(
            i.get('name', u'どれでも'), i.get('mode', u'どれでも'), i['count']))
  
        line.append(u'写真を調査')
        line.append(u'\\n'.join(goals))
        line.append(u'')

      elif info['quest']['type'] == 'phenomenBanish':
        goals = set()
        forced = False
        for i in info['phenomen']:
          goals.add(u'写真:{0} 異常:{1} x{2}'.format(
            i.get('scene', u'どれでも'), i.get('name', u'どれでも'), i['count']))

          if i['forced']:
            forced = True

        line.append(u'異常のある場所を調査' if forced else u'異常を調査または除去')
        line.append(u'\\n'.join(goals))
        line.append(u'')

      elif info['quest']['type'] == 'playMiniGames':
        goals = set()
        for i in info['games']:
          goals.add(u'パズル:{0} x{1}'.format(
            i.get('name', u'どれでも'), i['count']))

        line.append(u'パズルクリア')
        line.append(u'\\n'.join(goals))
        line.append(u'')

      elif info['quest']['type'] == 'increaseSceneLevel':
        goals = set()
        for i in info['levelup']:
          goals.add(u'{0}で{1}レベル'.format(
            i['name'], i['level']))

        line.append(u'レベルアップ')
        line.append(u'\\n'.join(goals))
        line.append(u'')

      elif info['quest']['type'] == 'collectibles':
        line.append(u'メダル集め')
        line.append(u'メダルを集める x{0}'.format(info['quest']['reward']['money']))
        line.append(u'')

      elif info['quest']['type'] == 'g5invest':
        line.append(u'広告')
        line.append(info['text'].get('hint', u''))
        line.append(u'')

      elif info['quest']['type'] == 'social':
        if info['quest']['social']['subtype'] == 'help':
          goal = u'友達をヘルプ x{0}'.format(info['quest']['social']['count'])
        elif info['quest']['social']['subtype'] == 'gift':
          goal = u'ギフトを送る x{0}'.format(info['quest']['social']['count'])
        elif info['quest']['social']['subtype'] == 'friend':
          goal = u'友達を追加 x{0}'.format(info['quest']['social']['count'])

        line.append(u'友達')
        line.append(goal)
        line.append(u'')

      elif info['quest']['type'] == 'buyItem':
        line.append(u'アイテムを買う')
        line.append(u'{0}を買う x1'.format(info['itemname']))
        line.append(u'')

      elif info['quest']['type'] == 'useItem':
        line.append(u'アイテムを使う')
        line.append(u'{0}を使う x1'.format(info['itemname']))
        line.append(u'')

      else:
        line.append(info['quest']['type'])
        line.append(u'')
        line.append(u'')

      rewards = []
      if info['quest']['reward']['crys']:
        rewards.append(u'クリスタル:{0}'.format(info['quest']['reward']['crys']))
      if info['quest']['reward']['exp']:
        rewards.append(u'経験:{0}'.format(info['quest']['reward']['exp']))
      if info['quest']['reward']['money']:
        rewards.append(u'ゴールド:{0}'.format(info['quest']['reward']['money']))

      line.append(u'\\n'.join(rewards))

      if 'diary' in info:
        line.append(info['diary']['TITLE'])
        line.append(info['diary']['PAGE'])

      try:
        print DELIM.join(line).encode('utf-8')
      except:
        print json.dumps(info, indent=2)
        print json.dumps(line, indent=2)
        raise


      for follow in info.get('depended_by', []):
        printinfo(follow, qinfo[follow])

    printinfo(key, val)

  #return

def main():
  if len(sys.argv) < 3:
    sys.stderr.write('Usage: {0} resdir lang [json]\n'.format(sys.argv[0]))
    sys.exit(2)

  qinfo = build_quest(sys.argv[1], sys.argv[2])

  if len(sys.argv) > 3 and sys.argv[3] == 'json':
    print json.dumps(qinfo, indent=2, sort_keys=True, ensure_ascii=False).encode('utf-8')
  else:
    print_quest(qinfo)

  #print json.dumps(quests, sort_keys=True, indent=2, ensure_ascii=False)
  #print json.dumps(textinfo, sort_keys=True, indent=2, ensure_ascii=False)

if __name__ == '__main__':
  main()
