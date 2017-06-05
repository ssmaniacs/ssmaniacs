#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ts=2 et
import sys
import os
import json
import base64
from xml.etree import ElementTree
from collections import OrderedDict
from TextInfo import load_textinfo


MODEID = {
  'text': 0,
  'night': 1,
  'siluet': 2,
  'part': 6,
  'parts': 6,
  'morph': 8,
  'couple': 10,
  'couples': 10,
}

ANOMALY = {
  'time': 1,
  'mirror': 2,
  'scrolleater': 3,
  'smoke': 4,
}
#IDS_PHENOMEN_1:失われた時間
#IDS_PHENOMEN_2:幽霊の鏡
#IDS_PHENOMEN_5:破れた写真
#IDS_PHENOMEN_3:巻物食らい
#IDS_PHENOMEN_4:神秘の煙
#IDS_PHENOMEN_10:呪い

#IDS_SCENE_TYPE_0:文字
#IDS_SCENE_TYPE_1:夜
#IDS_SCENE_TYPE_2:シルエット
#IDS_SCENE_TYPE_3:シルエット 夜
#IDS_SCENE_TYPE_4:文字替え
#IDS_SCENE_TYPE_5:文字替え 夜
#IDS_SCENE_TYPE_6:かけら
#IDS_SCENE_TYPE_7:かけら 夜
#IDS_SCENE_TYPE_8:モーフ
#IDS_SCENE_TYPE_9:モーフ 夜
#IDS_SCENE_TYPE_10:ペア

def load_iteminfo(resdir):
  '''アイテム情報を読み込む'''
  items = {}

  # アイテム基本情報 (ID, 種別)
  root = ElementTree.parse(os.path.join(resdir, '1024', 'properties', 'items.xml')).getroot()
  for item in root:
    id_ = int(item.get('id'))
    sectype = item.get('secType')
    if sectype is None:
      sectype = item.get('sectype')

    items[id_] = {
      'id': id_,
      'type': int(item.get('type')),
      'sectype': int(sectype),
      'found': [],
    }
    try:
      items[id_]['nogift'] = int(item.get('nogift'))
    except StandardError:
      pass

  # 通常入手可能なシーン・レベル
  with open(os.path.join(resdir, '1024', 'properties', 'loots.json'), 'r') as fh:
    jdata = json.load(fh)

  for s in jdata['scenes']:
    if 'scene_id' in s:
      where = 'scene'
      scid = s['scene_id']

    elif 'puzzle_id' in s:
      where = 'puzzle'
      scid = s['puzzle_id']
      if scid < 0:
        scid = -(scid)

    else:
      raise RuntimeError('No scene_id nor puzzle_id defined')

    for l in s['loots']:
      item = l['id']
      if item not in items:
        sys.stderr.write('Unknown item id {0} in {2}: {3} {1}\n'.format(item, json.dumps(lt, indent=2), where, scid))
        continue

      found = {
        where: scid,
        'level': l['level'],
        'chance': l['chance'],
        'type': l['type'],
      }

      items[item]['found'].append(found)

  # 特定のモード・状態で追加入手可能なもの
  root = ElementTree.parse(os.path.join(resdir, '1024', 'properties', 'additional_loots.xml')).getroot()

  for node in root:
    if node.tag != 'scene':
      continue

    try:
      chance = int(node.get('chance'))
    except StandardError:
      continue

    mode = node.get('name')
    type = node.get('type')

    if type == 'scenetype':
      if mode == 'anagram':
        cond = 'anomaly'
        mode = 10
      else:
        cond = 'mode'
        mode = MODEID[mode]
    else:
      cond = 'anomaly'
      mode = ANOMALY[mode]

    for l in node:
      try:
        item = int(l.get('item'))
      except StandardError:
        continue

      items[item]['found'].append({
        cond: mode,
        'chance': chance
      })

  # クエストで入手可能なシーン・モード
  with open(os.path.join(resdir, '1024', 'properties', 'quests.xml'), 'r') as fh:
    jdata = json.load(fh)

  for q in jdata['quests'].values():
    if 'findItem' not in q:
      continue

    for i in q['findItem'].values():
      item = i['itemId']
      if item not in items:
#        sys.stderr.write('Unknown item id {0} in quest {1}\n'.format(item, json.dumps(q, indent=2)))
        sys.stderr.write('Unknown item id {0} in quest {1}\n'.format(item, q['uid']))
        continue

      if 'lookInScenes' in i:
        for (scene, chance) in zip(i['lookInScenes']['sceneId'], i['lookInScenes']['chance']):
          items[item]['found'].append({
            'quest': q['uid'],
            'scene': scene,
            'chance': chance,
          })

      if 'lookInPuzzle' in i:
        for (puzzle, chance) in zip(i['lookInPuzzle']['puzzleId'], i['lookInPuzzle']['chance']):
          items[item]['found'].append({
            'quest': q['uid'],
            'puzzle': puzzle,
            'chance': chance,
          })

      if 'Chances' in i:
        if i['Chances']['type'] == 'anomaly':
          for (anomaly, chance) in zip(i['Chances']['anomaly'], i['Chances']['chance']):
            items[item]['found'].append({
              'quest': q['uid'],
              'anomaly': anomaly,
              'chance': chance,
            })

        elif i['Chances']['type'] == 'curse':
          for chance in i['Chances']['chance']:
            items[item]['found'].append({
              'quest': q['uid'],
              'anomaly': 10,
              'chance': chance,
            })

        elif i['Chances']['type'] == 'curse_scene':
          for (scene, chance) in zip(i['Chances']['scenes'], i['Chances']['chance']):
            items[item]['found'].append({
              'quest': q['uid'],
              'scene': scene,
              'anomaly': 10,
              'chance': chance,
            })

        elif i['Chances']['type'] == 'mode':
          for (mode, chance) in zip(i['Chances']['mode'], i['Chances']['chance']):
            items[item]['found'].append({
              'quest': q['uid'],
              'mode': MODEID[mode],
              'chance': chance,
            })

        elif i['Chances']['type'] == 'mode_scene':
          for (scene, mode, chance) in zip(i['Chances']['scenes'], i['Chances']['mode'], i['Chances']['chance']):
            items[item]['found'].append({
              'quest': q['uid'],
              'scene': scene,
              'mode': MODEID[mode],
              'chance': chance,
            })

        else:
          raise RuntimeError('Unknown "Chance" quest type: {1}'.format(json.dumps(q, indent=2)))


  return items


def output_json(iteminfo, collinfo, textinfo, dstdir, imgdir):
  def get_iteminfo(itemid):
    '''個々のアイテムの詳細情報を収集する'''
    info = {
      'id': itemid,
      'name': textinfo['ITEM'][itemid]['NAME'],
      'gift': (not iteminfo[itemid].get('nogift')),
      'icon': 'images/items/{0}.png'.format(itemid),
      'find': [],
      #'info': iteminfo[itemid],
    }

    # スペシャルケース：元データ内でエントリがダブっている
    if itemid == 2069:
      info['name'] = textinfo['ITEM'][itemid]['NAME'][-1]
      info['desc'] = textinfo['ITEM'][itemid]['INFO'][-1]

    elif isinstance(textinfo['ITEM'][itemid]['INFO'], basestring):
      info['desc'] = textinfo['ITEM'][itemid]['INFO']

    elif isinstance(textinfo['ITEM'][itemid]['INFO'], list):
      info['desc'] = u'?'.join(textinfo['ITEM'][itemid]['INFO'])

    if iteminfo[itemid]['type'] == 0:
      info['gift'] = False
      info['find'].append(u'遺物を組み合わせる')

    elif iteminfo[itemid]['type'] == 5:
      info['find'].append(u'コレクションを組み合わせる')

    elif iteminfo[itemid]['type'] == 4:
      for find in iteminfo[itemid]['found']:
        where = {}
        cond = []

        if 'quest' in find:
          where['quest'] = textinfo['QUEST'][find['quest']]['NAME']

        if 'scene' in find:
          where['scene'] = textinfo['SCENE'][find['scene']]['NAME']

        if 'puzzle' in find:
          where['puzzle'] = textinfo['PUZZLE'][find['puzzle']]['NAME']

        if 'mode' in find:
          cond.append(textinfo['SCENETYPE'][find['mode']]['NAME'] + u'モード')

        if 'anomaly' in find:
          cond.append(textinfo['PHENOMEN'][find['anomaly']]['NAME'] + u'の異常')

        if 'level' in find:
          cond.append(textinfo['LEVEL'][find['level'] - 1]['NAME'] + u'レベル以上')

        if 'chance' in find:
          where['prob'] = '{0}%'.format(find['chance'])

        if cond:
          where['cond'] = ', '.join(cond)

        info['find'].append(where)

    else:
      sys.stderr.write(json.dumps(iteminfo[itemid], indent=2))
      raise RuntimeError('unexpected item type')

    return info

  # アイテム情報をコレクション・遺物ごとに整理する
  collections = {}
  artifacts = {}

  for c in collinfo:
    if c['type'] == 'collection':
      target = collections
    else:
      target = artifacts

    if c['id'] in target:
      sys.stderr.write('Duplicate collection/artifact ID\n')
      sys.stderr.write(str(target[c['id']]) + '\n')
      sys.stderr.write(str(c) + '\n')
      raise RuntimeError('')

    target[c['id']] = {
      'id': c['id'],
      'name': textinfo[c['type'].upper()][c['id']]['NAME'],
      'items': [get_iteminfo(i) for i in c['items'] + [c['main_item_id']]],
      'charges': [
        {
          'id': i['id'],
          'count': i['count'],
          'name': textinfo['ITEM'][i['id']]['NAME']
        } for i in c['charges']],
      'rewards': [
        {
          'id': i['id'],
          'count': i['count'],
          'name': textinfo['ITEM'][i['id']]['NAME']
        } for i in c['rewards']],
    }

  # コレクションをページ（50項目）ごとに整理する
  collpages = []
  page = None
  idx = 1
  for id, coll in sorted(collections.items()):
    if page and len(page['colls']) >= 50:
      page['title'] = u'{0} {1}-{2}'.format(textinfo['IDS_COLLECTIONS'],
        page['colls'][0]['id'], page['colls'][-1]['id'])

      collpages.append(page)
      page = None

    if not page:
      page = {
        'id': u'collections_{0}'.format(idx),
        'colls': [],
      }
      idx += 1

    page['colls'].append(coll)

  if page:
      page['title'] = u'{0} {1}-{2}'.format(textinfo['IDS_COLLECTIONS'],
        page['colls'][0]['id'], page['colls'][-1]['id'])

      collpages.append(page)

  # 遺物をページ（50項目）ごとに整理する
  page = None
  idx = 1
  for id, coll in sorted(artifacts.items()):
    if page and len(page['colls']) >= 50:
      page['title'] = u'{0} {1}-{2}'.format(textinfo['IDS_ARTIFACTS'],
        page['colls'][0]['id'], page['colls'][-1]['id'])

      collpages.append(page)
      page = None

    if not page:
      page = {
        'id': u'artifacts_{0}'.format(idx),
        'colls': [],
      }
      idx += 1

    page['colls'].append(coll)

  if page:
      page['title'] = u'{0} {1}-{2}'.format(textinfo['IDS_ARTIFACTS'],
        page['colls'][0]['id'], page['colls'][-1]['id'])

      collpages.append(page)

  # インデックスJSを出力
  with open(os.path.join(dstdir, 'collections_idx.js'), 'w') as fh:
    sys.stderr.write('Exporting collections_idx.js\n')

    idx = [{'id': 'collections_all', 'title': u'{0} &amp; {1} (画像なし)'.format(
      textinfo['IDS_COLLECTIONS'], textinfo['IDS_ARTIFACTS'])}]
    idx += [{'id':x['id'], 'title':x['title'] + u' (画像あり)'} for x in collpages]

    fh.write('var collections =\n')
    fh.write(json.dumps(idx, indent=2, ensure_ascii=False).encode('utf-8'))
    fh.write(';\n')

  # 全ページ一括のJSONを出力（画像データなし）
  with open(os.path.join(dstdir, 'collections_all.json'), 'w') as fh:
    sys.stderr.write('Exporting collections_all.json\n')
    fh.write(json.dumps(collpages, indent=2, ensure_ascii=False).encode('utf-8'))

  # ページごとのJSONを出力（画像データ埋め込み）
  for page in collpages:
    sys.stderr.write('Exporting {0}.json\n'.format(page['id']))
    if imgdir:
      for coll in page['colls']:
        for item in coll['items']:
          with open(os.path.join(imgdir, 'items', '{0}.png'.format(item['id'])), 'r') as fh:
            item['data'] = 'data:image/png;base64,' + base64.b64encode(fh.read())

    with open(os.path.join(dstdir, page['id'] + '.json'), 'w') as fh:
      fh.write(json.dumps([page], indent=2, ensure_ascii=False).encode('utf-8'))


def main():
  try:
    (resdir, dstdir, lang, imgdir) = sys.argv[1:]
  except StandardError:
    sys.stderr.write('Usage: {0} resdir dstdir lang {{imgdir|-}}\n'.format(sys.argv[0]))
    sys.exit(2)

  textinfo = load_textinfo(resdir, lang)

  iteminfo = load_iteminfo(resdir)

  with open(os.path.join(resdir, '1024', 'properties', 'collections.json'), 'r') as fh:
    collinfo = json.load(fh)

  output_json(iteminfo, collinfo, textinfo, dstdir, imgdir if imgdir != '-' else None);


if __name__ == '__main__':
  main()
