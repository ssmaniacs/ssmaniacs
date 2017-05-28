#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ts=2 et
import sys
import os
import json
from xml.etree import ElementTree


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


def load_textfile(basedir, lang):
  '''表示用テキスト情報を読み込む'''
  if lang == 'en':
    filename = 'default.xml'
  else:
    filename = 'default_{0}.xml'.format(lang)

  textinfo = {}
  with open(os.path.join(basedir, '1024', 'properties', filename), 'r') as fh:
    for line in fh:
      if ':' in line:
        (key, val) = line.split(':', 1)
        textinfo[key] = val.strip()

  return textinfo


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
  'text':     'IDS_SCENE_TYPE_0',
  'night':    'IDS_SCENE_TYPE_1',
  'siluet':   'IDS_SCENE_TYPE_2',
  'part':     'IDS_SCENE_TYPE_6',
  'parts':    'IDS_SCENE_TYPE_6',
  'morph':    'IDS_SCENE_TYPE_8',
  'couple':   'IDS_SCENE_TYPE_10',
  'couples':  'IDS_SCENE_TYPE_10',
  'time':     'IDS_PHENOMEN_1',
  'mirror':   'IDS_PHENOMEN_2',
  'smoke':    'IDS_PHENOMEN_4',
  'scrolleater': 'IDS_PHENOMEN_3',
  'anagram':  'IDS_PHENOMEN_10',
  1:  'IDS_PHENOMEN_1',
  2:  'IDS_PHENOMEN_2',
  3:  'IDS_PHENOMEN_3',
  4:  'IDS_PHENOMEN_4',
}


'''
IDS_SCENE_TYPE_0:Text
IDS_SCENE_TYPE_1:Night
IDS_SCENE_TYPE_2:Silhouette
IDS_SCENE_TYPE_3:Silhouette Night
IDS_SCENE_TYPE_4:Anagram
IDS_SCENE_TYPE_5:Anagram Night
IDS_SCENE_TYPE_6:Pieces
IDS_SCENE_TYPE_7:Pieces Night
IDS_SCENE_TYPE_8:Morphs
IDS_SCENE_TYPE_9:Morphs Night
IDS_SCENE_TYPE_10:Pairs
IDS_SCENE_TYPE_11:Pairs Night
IDS_PHENOMEN_1:Lost Time
IDS_PHENOMEN_2:Ghostly Mirror
IDS_PHENOMEN_5:Torn Picture
IDS_PHENOMEN_3:Scroll Eater
IDS_PHENOMEN_4:Mystic Smoke
IDS_PHENOMEN_10:Curse
'''
  
def load_iteminfo(basedir):
  '''アイテム情報を読み込む'''
  items = {}

  # アイテム基本情報 (ID, 種別)
  root = ElementTree.parse(os.path.join(basedir, '1024', 'properties', 'items.xml')).getroot()
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
  with open(os.path.join(basedir, '1024', 'properties', 'loots.json'), 'r') as fh:
    jdata = json.load(fh)
    
  for s in jdata['scenes']:
    if 'scene_id' in s:
      where = 'scene'
      scid = s['scene_id']
    elif 'puzzle_id' in s:
      where = 'puzzle_id'
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

  # モード・状態で追加入手可能なもの
  root = ElementTree.parse(os.path.join(basedir, '1024', 'properties', 'additional_loots.xml')).getroot()
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
      cond = 'mode'
    else:
      cond = 'anomaly'
    
    for l in node:
      try:
        item = int(l.get(item))
      except StandardError:
        continue
      
      items[item]['found'].append({
        cond: MODEID[mode],
        'chance': chance
      })

  # クエストで入手可能なシーン・モード
  with open(os.path.join(basedir, '1024', 'properties', 'quests.xml'), 'r') as fh:
    jdata = json.load(fh)
    
  for q in jdata['quests'].values():
    if 'findItem' not in q:
      continue
      
    for i in q['findItem'].values():
      item = i['itemId']
      if item not in items:
        sys.stderr.write('Unknown item id {0} in quest {1}\n'.format(item, json.dumps(q, indent=2)))
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
              'anomaly': MODEID[anomaly],
              'chance': chance,
            })

        elif i['Chances']['type'] == 'curse':
          for chance in i['Chances']['chance']:
            items[item]['found'].append({
              'quest': q['uid'],
              'anomaly': 'IDS_PHENOMEN_10',
              'chance': chance,
            })
            
        elif i['Chances']['type'] == 'curse_scene':
          for (scene, chance) in zip(i['Chances']['scenes'], i['Chances']['chance']):
            items[item]['found'].append({
              'quest': q['uid'],
              'scene': scene,
              'anomaly': 'IDS_PHENOMEN_10',
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


def load_collections(basedir):
  '''コレクション情報を読み込む'''
  with open(os.path.join(basedir, '1024', 'properties', 'collections.json'), 'r') as fh:
    jdata = json.load(fh)

  collections = [[]]
  artifacts = []
  
  for c in jdata:
    if c['type'] == 'collection':
      if len(collections[-1]) >= 100:
        collections.append([])
        
      collections[-1].append(c)
    elif c['type'] == 'artifact':
      artifacts.append(c)
    else:
      print c
      raise RuntimeError('unknown type')

  return (collections, artifacts)



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
    (basedir, dstdir, lang) = sys.argv[1:]
  except StandardError:
    sys.stderr.write('Usage: {0} basedir dstdir lang\n'.format(sys.argv[0]))
    sys.exit(2)

  textinfo = load_textfile(basedir, lang)
  iteminfo = load_iteminfo(basedir)

  print json.dumps(iteminfo, indent=2, sort_keys=True)
  '''
  htmllist = write_index(collections, artifacts, textinfo, dstdir)

  for html in htmllist:
    write_collist(html, textinfo, iteminfo, dstdir)
  '''


if __name__ == '__main__':
  main()
