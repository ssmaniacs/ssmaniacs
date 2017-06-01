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

HTML_HEAD = '''<!DOCTYPE html>
<html>
  <head>
    <title>{title}</title>
    <meta charset='utf-8'>
    <meta name='viewport' content='width=device-width,initial-scale=1'>
  </head>
  <body>
'''
HTML_TAIL = '''
</body>
</html>
'''


ITEMTYPE = {
		0: 'powerups',
		1: 'hints',
		2: 'foods',
		3: 'specials(pandora boxes)',
		4: 'collections items',
		5: 'collections',
		6: 'others',
		8: 'power',
}
			
SECTYPE = {
		0: 'powerups',
		1: 'super amulets',
		2: 'energy',
		3: 'power',
		4: 'keys',
		5: 'charges',
		6: 'banish items',
		7: 'collections items',
		8: 'collections',
		9: 'loots',
		10: 'hints',
		11: 'specials(pandora boxes)',
}

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
    info = {
      'id': itemid,
      'name': textinfo['ITEM'][itemid]['NAME'],
      'desc': ''.join(textinfo['ITEM'][itemid]['INFO']),
      #'info': iteminfo[itemid],
      'gift': (not iteminfo.get('nogift')),
      'icon': 'images/items/{0}.png'.format(itemid),
      'find': [],
    }
    
    if imgdir:
      with open('{0}/items/{1}.png'.format(imgdir, itemid), 'r') as fh:
        info['data'] = 'data:image/png;base64,' + base64.b64encode(fh.read())
      
    if iteminfo[itemid]['type'] == 0:
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
          where['where'] = textinfo['SCENE'][find['scene']]['NAME']

        if 'puzzle' in find:
          where['where'] = textinfo['PUZZLE'][find['puzzle']]['NAME']

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
    
    
  collections = {}
  artifacts = {}
  
  for c in collinfo:
    if c['type'] == 'collection':
      target = collections
    else:
      target = artifacts
      
    target[c['id']] = {
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

  if imgdir:
    idx = 1
    output = {}
    limit = 50
    for (key, val) in sorted(collections.items()):
      if idx not in output:
        output[idx] = {}
        
      output[idx][key] = val
      if len(output[idx]) == limit:
        idx += 1

    for (key, val) in sorted(output.items()):
      with open(os.path.join(dstdir, 'collections_{0}.json').format(key), 'w') as fh:
          fh.write(json.dumps(val, indent=2, ensure_ascii=False).encode('utf-8'))

    with open(os.path.join(dstdir, 'artifacts.json').format(key), 'w') as fh:
      fh.write(json.dumps(artifacts, indent=2, ensure_ascii=False).encode('utf-8'))

  else:
    with open(os.path.join(dstdir, 'collections_all.json'), 'w') as fh:
      fh.write(json.dumps(
        {'collections': collections, 'artifacts': artifacts},
        indent=2, ensure_ascii=False).encode('utf-8'))

    
        
def write_index(collections, artifacts, textinfo, dstdir):
  '''索引ページを出力する'''
  with open(os.path.join(dstdir, 'collections.html'), 'w') as fh:
    title = 'Secret Society {0}'.format(textinfo['IDS_COLLECTIONS'])
    fh.write(HTML_HEAD.format(title=title))
    
    fh.write('''
<a href='index.html'>[HOME]</a><hr>
<h1>{title}</h1>
<ul>
'''.format(title=title))

    htmllist = []
    
    info = {
        'html': 'collections_all.html',
        'title': '全{0} &amp; {1} (画像なし)'.format(textinfo['IDS_COLLECTIONS'], textinfo['IDS_ARTIFACTS']),
        'list': collections + [artifacts],
        'sections': []
    }
    
    fh.write('<li><a href="{html}">{title}</a></li>'.format(
      html=info['html'], title=info['title']))

    htmllist.append(info)
    
    idx = 1
    caption = textinfo['IDS_COLLECTIONS']
    for c in collections:
      info = {
        'html': 'collections_{0}.html'.format(idx),
        'list': [c]
      }
      idx += 1
      
      if htmllist:
        info['prev'] = htmllist[-1]['html']
        htmllist[-1]['next'] = info['html']

      min_ = c[0]['id']
      max_ = c[-1]['id']
      info['title'] = '{cap} {min}-{max}'.format(cap=caption, min=min_, max=max_)
      htmllist[0]['sections'].append((info['html'], info['title']))

      fh.write('<li><a href="{html}">{title}</a></li>'.format(
        html=info['html'], title=info['title']))

      htmllist.append(info)

    info = {
      'html': 'artifacts.html',
      'title': textinfo['IDS_ARTIFACTS'],
      'list': [artifacts],
    }

    if htmllist:
      htmllist[0]['sections'].append((info['html'], info['title']))
      info['prev'] = htmllist[-1]['html']
      htmllist[-1]['next'] = info['html']
    
    htmllist.append(info)
    fh.write('<li><a href="{html}">{cap}</a></li>'.format(
        html=info['html'], cap=info['title']))

    fh.write('</ul>\n')
    fh.write(HTML_TAIL.format(title=title))
  
  return htmllist


def write_collist(colinfo, textinfo, iteminfo, dstdir):
  '''コレクションリストを出力する'''
  listall = (len(colinfo['list']) > 1)

  with open(os.path.join(dstdir, colinfo['html']), 'w') as fh:
    title = 'Secret Society {0}'.format(colinfo['title'])
    fh.write(HTML_HEAD.format(title=title))

    # ナビゲーションバーを出力
    navi = [
      "<a href='index.html'>[HOME]</a>",
      "<a href='collections.html'>[UP]</a>",
    ]
    
    if 'prev' in colinfo:
      navi.append("<a href='{0}'>[PREV]</a>".format(colinfo['prev']))
    else:
      navi.append("<font color=gray>[PREV]</font>")
      
    if 'next' in colinfo:
      navi.append("<a href='{0}'>[NEXT]</a>".format(colinfo['next']))
    else:
      navi.append("<font color=gray>[NEXT]</font>")

    fh.write('&nbsp;'.join(navi))

    # メインタイトルを出力
    fh.write('<hr>\n<h1>{0}</h1>\n'.format(colinfo['title']))
  
    # ALLリストの場合、セクションインデックスを出力
    if 'sections' in colinfo:
      fh.write('<ul>\n')

      for (h, t) in colinfo['sections']:
        fh.write('<li><a href="#{0}">{1}</a></li>\n'.format(h.split('.', 1)[0], t))

      fh.write('</ul>\n<hr>\n')

    # リストテーブルを出力
    secidx = 0
    
    for collist in colinfo['list']:
      if listall:
        (h, t) = colinfo['sections'][secidx]
        secidx += 1
        fh.write('<h2><a name="{0}">{1}</a></h2>\n'.format(h.split('.', 1)[0], t))

      if collist[0]['type'] == 'artifact':
        typename = textinfo['IDS_ARTIFACTS']
      else:
        typename = textinfo['IDS_COLLECTIONS']

      fh.write('''
    <table border='1' bgcolor='#FFDD88' cellpadding='5'>
    <tr>
    <th>No.</th>
    <th>{0}名</th>
    <th>アイテム1</th>
    <th>アイテム2</th>
    <th>アイテム3</th>
    <th>アイテム4</th>
    <th>アイテム5</th>
    <th>{0}</th>
    <th>エレメント</th>
    <th>報酬</th>
    <th>ギフト</th>
    </tr>
'''.format(typename))

      for c in collist:
        line = [
          '<tr>'
          '<td align="right">{0}</td>'.format(c['id']),
        ]

        if c['type'] == 'collection':
          name = textinfo['IDS_COLLECTION_NAME_{0}'.format(c['id'])]
        elif c['type'] == 'artifact':
          name = textinfo['IDS_ARTIFACT_NAME_{0}'.format(c['id'])]
        
        line.append('<td>{0}</td>'.format(name))
        
        nogift = 0
        
        for i in c['items'] + [c['main_item_id']]:
          name = textinfo['IDS_ITEM_NAME_{0}'.format(i)]

          if listall:
            line.append('<td>{name}</td>'.format(name=name))
          else:
            img = 'images/items/{0}.png'.format(i)
            line.append('<td align="center" valign="top" width="120"><img src="{img}"><br>{name}</td>'.format(name=name, img=img))

          nogift += iteminfo.get(i, 0)

        elem = []
        for e in c['charges']:
          elem.append('{0} x{1}'.format(textinfo['IDS_ITEM_NAME_{0}'.format(e['id'])], e['count']))

        line.append('<td>{0}</td>'.format('<br>'.join(elem)))

        rew = []
        for r in c['rewards']:
          rew.append('{0} x{1}'.format(textinfo['IDS_ITEM_NAME_{0}'.format(r['id'])], r['count']))

        line.append('<td>{0}</td>'.format('<br>'.join(rew)))
        
        if nogift > 1 or c['type'] == 'artifact':
          line.append('<td bgcolor=#dd4444>NG</td>')
        else:
          line.append('<td>OK</td>')
        
        line.append('</tr>')
        line.append('')

        fh.write('\n'.join(line))

      fh.write('</table>\n')
      
      if listall:
        fh.write('<div align="right"><a href="#">[TOP]</a></div>\n')

    fh.write('<hr>\n')
    fh.write('&nbsp;'.join(navi))
    fh.write(HTML_TAIL)


def main():
  try:
    (resdir, dstdir, lang, imgdir) = sys.argv[1:]
  except StandardError:
    sys.stderr.write('Usage: {0} resdir dstdir lang {{imgdir|-}}\n'.format(sys.argv[0]))
    sys.exit(2)

  textinfo = load_textinfo(resdir, lang)
  #print json.dumps(textinfo, indent=2, sort_keys=True, ensure_ascii=False).encode('utf-8')
  
  iteminfo = load_iteminfo(resdir)

  with open(os.path.join(resdir, '1024', 'properties', 'collections.json'), 'r') as fh:
    collinfo = json.load(fh)

  output_json(iteminfo, collinfo, textinfo, dstdir, imgdir if imgdir != '-' else None);
  
  #print json.dumps(iteminfo, indent=2, sort_keys=True)
  '''
  htmllist = write_index(collections, artifacts, textinfo, dstdir)

  for html in htmllist:
    write_collist(html, textinfo, iteminfo, dstdir)
  '''


if __name__ == '__main__':
  main()
