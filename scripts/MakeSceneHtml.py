#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ts=2 et
'''各シーンのパラメータ、オブジェクトリストを作成する

INPUT:
- 1024/properties/data_scenes.xml
  シーンID、シーンリソースファイル名、その他メインパラメータ

- 1024/properties/default(_lang).xml
  シーン名、テキストモードオブジェクト名

- 1024/properties/data_balance.json
  アンロックパズル関連（ピース数、制限時間、コスト（コイン？））

- 1024/properties/unlock_scene_levels.xml
  シーンアンロック可能レベル

- 1024/properties/unlock_scene_loots.xml
  シーンアンロック時の報酬
  
- 1024/properties/scene_unlocks.xml
  シーンアンロックコスト

- 1024/levles/scene_<ID>.xml
    オブジェクト情報（内部名、イメージパスなど）
'''

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

  if lang == 'ja':
    textinfo['IDS_PHENOMEN'] = '異常'
  else:
    textinfo['IDS_PHENOMEN'] = 'Anomaly'

  return textinfo


def load_sceneinfo(basedir):
  '''シーン一覧を読み込む'''
  sceneinfo = {}

  # XMLファイルパス、レベルパラメータ
  root = ElementTree.parse(os.path.join(basedir, '1024',
    'properties', 'data_scenes.xml')).getroot()
 
  for scene in root.findall('scene'):
    id_ = int(scene.get('id'))
    sceneinfo[id_] = {
      'id': id_,
      'xml': scene.get('xml')
    }

    lvlist = []
    for lv in scene.findall('level'):
      level = {}

      for name in ('params', 'phenomen', 'text', 'parts',
        'couples', 'morphs', 'allowed', 'types_chances'):
        level[name] = lv.find(name).attrib

        for k in level[name].keys():
          level[name][k] = int(level[name][k])

      lvlist.append(level)

    sceneinfo[id_]['levels'] = lvlist

  # アンロックパズルパラメータ
  with open(os.path.join(basedir, '1024', 'properties', 'data_balance.json'), 'r') as fh:
    jdata = json.load(fh)

  for scene in jdata['UnlockScenesInfo']:
    sceneinfo[scene['scene_id']]['unlock'] = {
      'pieces': scene['first_unlock_cut'], # ピースの分割パターン？
      'time': scene['time'],
      'skip_cost': scene['unlock_cost'],
      'diary': scene['diaryPageId'],
    }

  # アンロック可能レベル
  root = ElementTree.parse(os.path.join(basedir, '1024',
    'properties', 'unlock_scene_levels.xml')).getroot()

  for scene in root.findall('Scene'):
    id_ = int(scene.get('sceneid'))
    sceneinfo[id_]['unlock']['early_level'] = int(scene.get('early_unlock_level'))
    sceneinfo[id_]['unlock']['real_level'] = int(scene.get('really_unlock_level'))

  # アンロック報酬
  root = ElementTree.parse(os.path.join(basedir, '1024',
    'properties', 'unlock_scene_loots.xml')).getroot()

  for scene in root.findall('Scene'):
    id_ = int(scene.get('sceneid'))
    if id_ != -1:
      sceneinfo[id_]['unlock']['money'] = int(scene.get('money'))
      sceneinfo[id_]['unlock']['exp'] = int(scene.get('exp'))
    else:
      money = int(scene.get('money'))
      exp = int(scene.get('exp'))
      for v in sceneinfo.values():
        if v['unlock']['money']:
          v['unlock']['skip_money'] = money
          v['unlock']['skip_exp'] = exp

  # アンロックコスト
  root = ElementTree.parse(os.path.join(basedir, '1024',
    'properties', 'scene_unlocks.xml')).getroot()
  
  id_ = 0
  for scene in root:
    # シーンがID順に記載されていると思われるが、IDが明示されていない。
    id_ += 1
    ul = scene.find('Unlock_1')
    if ul is not None:  # ベネチアには Unlock_1 エレメントなし
      sceneinfo[id_]['unlock']['cost'] = int(ul.get('cost'))
      sceneinfo[id_]['unlock']['gold'] = int(ul.get('gold'))
      sceneinfo[id_]['unlock']['energy'] = int(ul.get('energy'))

  return sceneinfo


def load_sceneobj(basedir, filename):
  '''シーンのオブジェクト情報を読み込む'''
  tree = ElementTree.parse(os.path.join(basedir, '1024', filename))
  root = tree.getroot()

  objlist = {}

  for objtype in root.findall('objects/*'):

    if objtype.tag == 'standart':
      objlist['norm'] = []

      for obj in objtype.findall('gray_object'):
        img = [
          obj.get('list_name'),
          obj.get('list_sil').rsplit('/', 1)[-1]
        ]
        for pic in obj.findall('clickzone/pic'):
          n = pic.get('texture').rsplit('/', 1)[-1]
          w = int(pic.get('w'))
          h = int(pic.get('h'))
          img.append((n, w, h))

        objlist['norm'].append(img)

    elif objtype.tag == 'part':
      objlist['part'] = []

      for part in objtype.findall('part_object'):
        img = [part.get('image').rsplit('/', 1)[-1]]
        for obj in part.findall('gray_object'):
          img.append(obj.get('list_part').rsplit('/', 1)[-1])

        objlist['part'].append(img)

    elif objtype.tag == 'morph':
      objlist['morph'] = []

      for obj in objtype.findall('gray_object'):
        pic1 = obj.find('clickzone/pic1')
        n1 = pic1.get('texture').rsplit('/', 1)[-1]
        w1 = int(pic1.get('w'))
        h1 = int(pic1.get('h'))
        
        pic2 = obj.find('clickzone/pic2')
        n2 = pic2.get('texture').rsplit('/', 1)[-1]
        w2 = int(pic2.get('w'))
        h2 = int(pic2.get('h'))
        objlist['morph'].append(((n1, w1, h1), (n2, w2, h2)))

  return objlist


def write_index(sceneinfo, dstdir):
  '''索引ページを出力する'''
  with open(os.path.join(dstdir, 'scenes.html'), 'w') as fh:
    fh.write(HTML_HEAD.format(title='Secret Society シーン'))
    
    fh.write('''
<a href='index.html'>[HOME]</a><hr>
<h1>Secret Society シーン</h1>
<ul>
''')

    for scene in sceneinfo:
      fh.write('<li><a href="{0}">{1}</a></li>\n'.format(
        scene['html'], scene['name'].encode('utf-8')))

    fh.write('''
</ul>
<hr>
<a href='index.html'>[HOME]</a>
</body>
</html>
''')


def write_html(scene, sceneobj, textinfo, dstdir):
  '''シーン情報HTMLを書き出す'''
  scenename = scene['name'].encode('utf-8')
  
  with open(os.path.join(dstdir, scene['html']), 'w') as fh:
    title = 'Secret Society - {0}'.format(scenename)
    fh.write(HTML_HEAD.format(title=title))

    navi = [
      "<a href='index.html'>[HOME]</a>",
      "<a href='scenes.html'>[UP]</a>",
    ]

    if 'prev' in scene:
      navi.append("<a href='{0}'>[PREV]</a>".format(scene['prev']))
    else:
      navi.append("<font color=gray>[PREV]</font>")
      
    if 'next' in scene:
      navi.append("<a href='{0}'>[NEXT]</a>".format(scene['next']))
    else:
      navi.append("<font color=gray>[NEXT]</font>")

    navi.append('')

    fh.write('&nbsp;'.join(navi))
    fh.write('<hr>\n')

    fh.write('<h1>{0}</h1>\n'.format(scenename))

    """
    # アンロックパラメータ情報出力
    fh.write('<hr><h2>アンロック情報</h2>\n')

    fh.write('''
<table border='1' cellpadding='5'>
<tr>
<th colspan=2>アンロック可能レベル</th>
<th colspan=5>アンロックパズル</th>
<th colspan=2>クリア報酬</th>
<th colspan=2>スキップ時報酬</th>
</tr>
<tr>
<th>クリスタル使用</th>
<th>クリスタルなし</th>
<th>コスト</th>
<th>コイン</th>
<th>エネルギー</th>
<th>制限時間</th>
<th>スキップコスト</th>
<th>コイン</th>
<th>経験値</th>
<th>コイン</th>
<th>経験値</th>
</tr>
''')

    ul = scene['unlock']
      
    scinfo = [
      '<tr>',
    ]
    
    for n in ('early_level','real_level','cost','gold','energy',
      'time','skip_cost','money','exp','skip_money','skip_exp'):
      v = ul.get(n)
      scinfo.append('<td align="right">{0}</td>'.format(v if v else '<br>'))

    scinfo.append('</tr>')
    scinfo.append('</table>')
    scinfo.append('')
    fh.write('\n'.join(scinfo))
    """

    # シーンパラメータ情報出力
    levelnames = [textinfo['IDS_SCENE_STAGE_{0}'.format(n)] for n in range(0, 9)]

    fh.write('<table border="1" cellpadding="5">')

    head = [
      '<tr>',
      '<th colspan="2"><br></th>',
    ]

    for i in range(len(levelnames)):
      head.append('<th bgcolor="#ffdd88">{0}</th>'.format(levelnames[i]))

    head.append('</tr>')
    head.append('')
    header = '\n'.join(head)


    line = [
      '<tr>',
      '<th colspan="2"><br></th>',
    ]

    for i in range(len(levelnames)):
      line.append(
        '<th bgcolor="#ffdd88" valign="top"><img src="images/border{0}.png" width="100%"><br>{1}</th>'.format(i, levelnames[i]))
      head.append('<th>{0}</th>'.format(levelnames[i]))

    line.append('</tr>')
    line.append('')
    fh.write('\n'.join(line))

    # 消費エネルギー
    line = [
      '<tr>',
      '<td colspan="2">消費エネルギー</td>'
    ]
    
    for lv in scene['levels']:
      line.append('<td align="right">{0}</td>'.format(lv['params']['energy']))

    line.append('</tr>')
    line.append('')
    fh.write('\n'.join(line))

    # 消費アイテム
    line = [
      '<tr>',
      '<td colspan="2">消費アイテム</td>'
    ]
    
    for lv in scene['levels']:
      try:
        if lv['params'].get('firefly'):
          text = '{0} x{1}'.format(
          textinfo['IDS_ITEM_NAME_{0}'.format(lv['params']['fireflyId'])],
          lv['params']['firefly']
        )
        else:
          text = '<br>'
      except:
        print json.dumps(lv, indent=2)
        raise

      line.append('<td align="right">{0}</td>'.format(text))

    line.append('</tr>')
    line.append('')
    fh.write('\n'.join(line))

    line = [
      '<tr>',
      '<td colspan="2">獲得コイン</td>'
    ]

    for lv in scene['levels']:
      line.append('<td align="right">{0}</td>'.format(lv['params']['money']))

    line.append('</tr>')
    line.append('')
    fh.write('\n'.join(line))

    line = [
      '<tr>',
      '<td colspan="2">獲得経験値</td>'
    ]
    
    for lv in scene['levels']:
      line.append('<td align="right">{0}</td>'.format(lv['params']['exp']))

    line.append('</tr>')
    line.append('')
    fh.write('\n'.join(line))

    line = [
      '<tr>',
      '<td colspan="2">進捗%</td>'
    ]
    for lv in scene['levels']:
      line.append('<td align="right">{0:4.2f}%<br>(100/{1})</td>'.format(
        100.0 / lv['params']['progress'], lv['params']['progress']))

    line.append('</tr>')
    line.append('')
    fh.write('\n'.join(line))

    fh.write(header)

    # 文字モード
    line = [
      '<tr>',
      '<td rowspan="3">{0}</td>'.format(textinfo['IDS_SCENE_TYPE_0']),
      '<td>確率</td>',
    ]
    for lv in scene['levels']:
      chance = lv['types_chances'].get('text')
      if chance:
        line.append('<td align="right">{0}%</td>'.format(chance))
      else:
        line.append('<td bgcolor="silver"></br></td>')

    line.append('</tr>')
    line.append('')
    fh.write('\n'.join(line))


    line = [
      '<tr>',
      '<td>時間</td>',
    ]
    for lv in scene['levels']:
      if lv['types_chances'].get('text'):
        line.append('<td align="right">{0}秒</td>'.format(lv['text']['time']))
      else:
        line.append('<td bgcolor="silver"></br></td>')

    line.append('</tr>')
    line.append('')
    fh.write('\n'.join(line))

    line = [
      '<tr>',
      '<td>探索</td>',
    ]
    for lv in scene['levels']:
      if lv['types_chances'].get('text'):
        lv['text']['total'] = lv['text']['easy'] + lv['text']['normal'] + lv['text']['hard']
        line.append('<td align="right">{0}個</td>'.format(lv['text']['total']))
      else:
        line.append('<td bgcolor="silver"></br></td>')

    line.append('</tr>')
    line.append('')
    fh.write('\n'.join(line))

    # 夜モード
    line = [
      '<tr>',
      '<td rowspan="3">{0}</td>'.format(textinfo['IDS_SCENE_TYPE_1']),
      '<td>確率</td>',
    ]
    for lv in scene['levels']:
      chance = lv['types_chances'].get('text_dark')
      if chance:
        line.append('<td align="right">{0}%</td>'.format(chance))
      else:
        line.append('<td bgcolor="silver"></br></td>')

    line.append('</tr>')
    line.append('')
    fh.write('\n'.join(line))

    line = [
      '<tr>',
      '<td>時間</td>',
    ]
    for lv in scene['levels']:
      if lv['types_chances'].get('text_dark'):
        line.append('<td align="right">{0}秒</td>'.format(lv['text']['dark_time']))
      else:
        line.append('<td bgcolor="silver"></br></td>')

    line.append('</tr>')
    line.append('')
    fh.write('\n'.join(line))

    line = [
      '<tr>',
      '<td>探索</td>',
    ]
    for lv in scene['levels']:
      if lv['types_chances'].get('text_dark'):
        line.append('<td align="right">{0}個</td>'.format(lv['text']['total']))
      else:
        line.append('<td bgcolor="silver"></br></td>')

    line.append('</tr>')
    line.append('')
    fh.write('\n'.join(line))

    # シルエットモード
    line = [
      '<tr>',
      '<td rowspan="3">{0}</td>'.format(textinfo['IDS_SCENE_TYPE_2']),
      '<td>確率</td>',
    ]
    for lv in scene['levels']:
      chance = lv['types_chances'].get('siluet')
      if chance:
        line.append('<td align="right">{0}%</td>'.format(chance))
      else:
        line.append('<td bgcolor="silver"></br></td>')

    line.append('</tr>')
    line.append('')
    fh.write('\n'.join(line))

    line = [
      '<tr>',
      '<td>時間</td>',
    ]
    for lv in scene['levels']:
      if lv['types_chances'].get('siluet'):
        line.append('<td align="right">{0}秒</td>'.format(lv['text']['time']))
      else:
        line.append('<td bgcolor="silver"></br></td>')

    line.append('</tr>')
    line.append('')
    fh.write('\n'.join(line))

    line = [
      '<tr>',
      '<td>探索</td>',
    ]
    for lv in scene['levels']:
      if lv['types_chances'].get('siluet'):
        line.append('<td align="right">{0}個</td>'.format(lv['text']['total']))
      else:
        line.append('<td bgcolor="silver"></br></td>')

    line.append('</tr>')
    line.append('')
    fh.write('\n'.join(line))

    fh.write(header)

    # かけらモード
    line = [
      '<tr>',
      '<td rowspan="3">{0}</td>'.format(textinfo['IDS_SCENE_TYPE_6']),
      '<td>確率</td>',
    ]
    for lv in scene['levels']:
      chance = lv['types_chances'].get('part')
      if chance:
        line.append('<td align="right">{0}%</td>'.format(chance))
      else:
        line.append('<td bgcolor="silver"></br></td>')

    line.append('</tr>')
    line.append('')
    fh.write('\n'.join(line))

    line = [
      '<tr>',
      '<td>時間</td>',
    ]
    for lv in scene['levels']:
      if lv['types_chances'].get('part'):
        line.append('<td align="right">{0}秒</td>'.format(lv['parts']['time']))
      else:
        line.append('<td bgcolor="silver"></br></td>')

    line.append('</tr>')
    line.append('')
    fh.write('\n'.join(line))

    line = [
      '<tr>',
      '<td>探索</td>',
    ]
    for lv in scene['levels']:
      if lv['types_chances'].get('part'):
        num = lv['parts']['part_easy'] + lv['parts']['part_normal'] + lv['parts']['part_hard']
        line.append('<td align="right">{0}組({1}個)</td>'.format(
          lv['parts']['parts_num'], lv['parts']['parts_num'] * num))
      else:
        line.append('<td bgcolor="silver"></br></td>')

    line.append('</tr>')
    line.append('')
    fh.write('\n'.join(line))


    # モーフモード
    line = [
      '<tr>',
      '<td rowspan="3">{0}</td>'.format(textinfo['IDS_SCENE_TYPE_8']),
      '<td>確率</td>',
    ]
    for lv in scene['levels']:
      chance = lv['types_chances'].get('morph')
      if chance:
        line.append('<td align="right">{0}%</td>'.format(chance))
      else:
        line.append('<td bgcolor="silver"></br></td>')

    line.append('</tr>')
    line.append('')
    fh.write('\n'.join(line))

    line = [
      '<tr>',
      '<td>時間</td>',
    ]
    for lv in scene['levels']:
      if lv['types_chances'].get('morph'):
        line.append('<td align="right">{0}秒</td>'.format(lv['morphs']['time']))
      else:
        line.append('<td bgcolor="silver"></br></td>')

    line.append('</tr>')
    line.append('')
    fh.write('\n'.join(line))

    line = [
      '<tr>',
      '<td>探索</td>',
    ]
    for lv in scene['levels']:
      if lv['types_chances'].get('morph'):
        num = lv['morphs']['morph_easy'] + lv['morphs']['morph_normal'] + lv['morphs']['morph_hard']
        line.append('<td align="right">{0}個</td>'.format(num))
      else:
        line.append('<td bgcolor="silver"></br></td>')

    line.append('</tr>')
    line.append('')
    fh.write('\n'.join(line))

    # ペアモード
    line = [
      '<tr>',
      '<td rowspan="3">{0}</td>'.format(textinfo['IDS_SCENE_TYPE_10']),
      '<td>確率</td>',
    ]
    for lv in scene['levels']:
      chance = lv['types_chances'].get('couple')
      if chance:
        line.append('<td align="right">{0}%</td>'.format(chance))
      else:
        line.append('<td bgcolor="silver"></br></td>')

    line.append('</tr>')
    line.append('')
    fh.write('\n'.join(line))

    line = [
      '<tr>',
      '<td>時間</td>',
    ]
    for lv in scene['levels']:
      if lv['types_chances'].get('couple'):
        line.append('<td align="right">{0}秒</td>'.format(lv['couples']['time']))
      else:
        line.append('<td bgcolor="silver"></br></td>')

    line.append('</tr>')
    line.append('')
    fh.write('\n'.join(line))

    line = [
      '<tr>',
      '<td>探索</td>',
    ]
    for lv in scene['levels']:
      if lv['types_chances'].get('couple'):
        num = lv['couples']['couples_easy'] + lv['couples']['couples_normal'] + lv['couples']['couples_hard'] + lv['couples']['couples_very_easy'] + lv['couples']['couples_very_hard']
        line.append('<td align="right">{0}組({1}個)</td>'.format(num, num * 2))
      else:
        line.append('<td bgcolor="silver"></br></td>')

    line.append('</tr>')
    line.append('')
    fh.write('\n'.join(line))


    # 異常＆呪い
    line = [
      '<tr>',
      '<td rowspan="2">{0}&amp;{1}</td>'.format(
        textinfo['IDS_PHENOMEN'], textinfo['IDS_PHENOMEN_10']),
      '<td>時間</td>',
    ]
    for lv in scene['levels']:
      line.append('<td align="right">{0}秒</td>'.format(lv['phenomen']['time']))

    line.append('</tr>')
    line.append('')
    fh.write('\n'.join(line))

    line = [
      '<tr>',
      '<td>探索</td>',
    ]
    for lv in scene['levels']:
      line.append('<td align="right">{0}個</td>'.format(lv['text']['total']))

    line.append('</tr>')
    line.append('')
    fh.write('\n'.join(line))


    fh.write('</table>\n')
    fh.write('<div align="right"><a href="#">[TOP]</a></div>\n')

    # 通常モードオブジェクト
    fh.write('<hr>\n')
    fh.write('<h2>{0}, {1}, {2}, {3}</h2>\n'.format(
      textinfo['IDS_SCENE_TYPE_0'], # IDS_SCENE_TYPE_0:文字
      textinfo['IDS_SCENE_TYPE_1'], # IDS_SCENE_TYPE_1:夜
      textinfo['IDS_SCENE_TYPE_2'], # IDS_SCENE_TYPE_2:シルエット
      textinfo['IDS_SCENE_TYPE_10'],# IDS_SCENE_TYPE_10:ペア
    ))

    fh.write('''
<table border='1' cellpadding='5' bgcolor='#FFDD88'>
<tr><th>{text}</th><th>{sils}</th><th>Sample</th></tr>
'''.format(text=textinfo['IDS_SCENE_TYPE_0'], sils=textinfo['IDS_SCENE_TYPE_2']))

    for obj in sceneobj['norm']:
      name = obj.pop(0)
      sceneid = name.split('.', 1)[0]

      sil = obj.pop(0)
      silimg = 'images/{0}.sils/{1}.png'.format(sceneid, sil)
      
      (norm, w, h) = obj.pop(0)
      normimg = 'images/{0}.form/{1}.png'.format(sceneid, norm)

      if w > h:
        size = " width=85"
      else:
        size = " height=90"

      objinfo = [
        '<tr>',
        '<td>{0}</td>'.format(textinfo[name]),
        '<td align="center"><img src="{0}"></td>'.format(silimg),
        '<td align="center"><img src="{0}"{1}></td>'.format(normimg, size),
      ]

      objinfo.append('</tr>')
      objinfo.append('')

      fh.write('\n'.join(objinfo))

    fh.write('</table>\n')
    fh.write('<div align="right"><a href="#">[TOP]</a></div>\n')

    # かけらモードオブジェクト
    fh.write('<hr>\n')
    fh.write('<h2>{0}</h2>\n'.format(
      textinfo['IDS_SCENE_TYPE_6'], # IDS_SCENE_TYPE_6:かけら
    ))

    fh.write('''
<table border='1' cellpadding='5' bgcolor='#FFDD88'>
<tr><th>ALL</th><th>1</th><th>2</th><th>3</th><th>4</th><th>5</th></tr>
''')

    for obj in sceneobj['part']:
      fh.write('<tr>\n')
      for name in obj:
        path = 'images/{0}.part/{1}.png'.format(sceneid, name)
        fh.write('<td align="center"><img src="{0}"></td>\n'.format(path))
      fh.write('</tr>\n')

    fh.write('</table>\n')
    fh.write('<div align="right"><a href="#">[TOP]</a></div>\n')

    # モーフモードオブジェクト
    fh.write('<hr>\n')
    fh.write('<h2>{0}</h2>\n'.format(
      textinfo['IDS_SCENE_TYPE_8'], # IDS_SCENE_TYPE_8:モーフ
    ))

    fh.write('''
<table border='1' cellpadding='5' bgcolor='#FFDD88'>
<tr><th>{0}(1)</th><th>{0}(2)</th></tr>
'''.format(textinfo['IDS_SCENE_TYPE_8']))

    for obj in sceneobj['morph']:
      fh.write('<tr>\n')

      for (name, w, h) in obj:
        path = 'images/{0}.morph/{1}.png'.format(sceneid, name)
        if w > h:
          size = ' width=85'
        else:
          size = ' height=90'

        fh.write('<td align="center"><img src="{0}"{1}></td>\n'.format(path, size))

      fh.write('</tr>\n')

    fh.write('</table>\n')
    fh.write('<div align="right"><a href="#">[TOP]</a></div>\n')

    fh.write('<hr\n')
    fh.write('&nbsp;'.join(navi))
    fh.write(HTML_TAIL)


def main():
  try:
    (basedir, dstdir, lang) = sys.argv[1:]
  except StandardError:
    sys.stderr.write('Usage: {0} basedir dstdir lang\n'.format(sys.argv[0]))
    sys.exit(2)

  textinfo = load_textfile(basedir, lang)

  sceneinfo = load_sceneinfo(basedir)

  scenelist = []
  for (id_, scene) in sorted(sceneinfo.items()):
    scene['name'] = textinfo['IDS_SCENE_NAME_{0}'.format(id_)].decode('utf-8')[1:-1]
    scene['html'] = 'scene_{0}.html'.format(id_)

    if len(scenelist):
      scenelist[-1]['next'] = scene['html']
      scene['prev'] = scenelist[-1]['html']

    scenelist.append(scene)

  write_index(scenelist, dstdir)

  for scene in scenelist:
    print scene['id'], scene['name']
    sceneobj = load_sceneobj(basedir, scene['xml'])
    write_html(scene, sceneobj, textinfo, dstdir)


if __name__ == '__main__':
  main()
