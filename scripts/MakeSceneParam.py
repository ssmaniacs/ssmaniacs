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
import re
import json
import base64
from xml.etree import ElementTree
from collections import OrderedDict


def load_textfile(resdir, lang):
  '''表示用テキスト情報を読み込む'''
  if lang == 'en':
    filename = 'default.xml'
  else:
    filename = 'default_{0}.xml'.format(lang)

  textinfo = {}
  with open(os.path.join(resdir, '1024', 'properties', filename), 'r') as fh:
    for line in fh:
      if ':' in line:
        (key, val) = line.split(':', 1)
        textinfo[key] = val.strip()

  if lang == 'ja':
    textinfo['IDS_PHENOMEN'] = '異常'
  else:
    textinfo['IDS_PHENOMEN'] = 'Anomaly'

  return textinfo


def load_sceneinfo(resdir):
  '''シーン一覧を読み込む'''
  sceneinfo = {}

  # XMLファイルパス、レベルパラメータ
  root = ElementTree.parse(os.path.join(resdir, '1024',
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
  with open(os.path.join(resdir, '1024', 'properties', 'data_balance.json'), 'r') as fh:
    jdata = json.load(fh)

  for scene in jdata['UnlockScenesInfo']:
    sceneinfo[scene['scene_id']]['unlock'] = {
      'pieces': scene['first_unlock_cut'], # ピースの分割パターン？
      'time': scene['time'],
      'skip_cost': scene['unlock_cost'],
      'diary': scene['diaryPageId'],
    }

  # アンロック可能レベル
  root = ElementTree.parse(os.path.join(resdir, '1024',
    'properties', 'unlock_scene_levels.xml')).getroot()

  for scene in root.findall('Scene'):
    id_ = int(scene.get('sceneid'))
    sceneinfo[id_]['unlock']['early_level'] = int(scene.get('early_unlock_level'))
    sceneinfo[id_]['unlock']['real_level'] = int(scene.get('really_unlock_level'))

  # アンロック報酬
  root = ElementTree.parse(os.path.join(resdir, '1024',
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
  root = ElementTree.parse(os.path.join(resdir, '1024',
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


def load_sceneobj(resdir, filename):
  '''シーンのオブジェクト情報を読み込む'''
  tree = ElementTree.parse(os.path.join(resdir, '1024', filename))
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
  sclist = [{'id': x['id'], 'name': x['name']} for x in sceneinfo]

  with open(os.path.join(dstdir, 'scene_idx.js'), 'w') as fh:
    fh.write('var scene_list =\n')
    fh.write(json.dumps(sclist, indent=2, ensure_ascii=False).encode('utf-8'))
    fh.write(';\n')


def write_json(scene, sceneobj, textinfo, imgdir, dstdir):
  '''シーン情報JSONを書き出す'''
  jdata = OrderedDict()

  # シーン基本情報
  jdata['id'] = scene['id']
  jdata['name'] = scene['name']

  # 各パラメータをレベル別に
  jdata['energy'] = []
  jdata['charge'] = []
  jdata['coins'] = []
  jdata['expoints'] = []
  jdata['progress'] = []
  jdata['text-prb'] = []
  jdata['text-sec'] = []
  jdata['text-obj'] = []
  jdata['night-prb'] = []
  jdata['night-sec'] = []
  jdata['night-obj'] = []
  jdata['sil-prb'] = []
  jdata['sil-sec'] = []
  jdata['sil-obj'] = []
  jdata['part-prb'] = []
  jdata['part-sec'] = []
  jdata['part-obj'] = []
  jdata['morph-prb'] = []
  jdata['morph-sec'] = []
  jdata['morph-obj'] = []
  jdata['pair-prb'] = []
  jdata['pair-sec'] = []
  jdata['pair-obj'] = []
  jdata['anom-sec'] = []
  jdata['anom-obj'] = []

  for lv in scene['levels']:
    p = lv['params']

    jdata['energy'].append(p['energy'])

    ff = p.get('firefly')
    if ff:
      ffname = textinfo['IDS_ITEM_NAME_{0}'.format(p['fireflyId'])].decode('utf-8')
      jdata['charge'].append(u'{0} x{1}'.format(ffname, ff))
    else:
      jdata['charge'].append(None)

    jdata['coins'].append(p['money'])
    jdata['expoints'].append(p['exp'])
    jdata['progress'].append([
      '{0:4.2f}%'.format(100.0 / p['progress']),
      '(100/{0})'.format(p['progress'])])

    chance = lv['types_chances'].get('text')
    if chance:
      jdata['text-prb'].append(chance)
      jdata['text-sec'].append(lv['text']['time'])
      jdata['text-obj'].append(lv['text']['easy'] + lv['text']['normal'] + lv['text']['hard'])
    else:
      jdata['text-prb'].append(None)
      jdata['text-sec'].append(None)
      jdata['text-obj'].append(None)

    chance = lv['types_chances'].get('text_dark')
    if chance:
      jdata['night-prb'].append(chance)
      jdata['night-sec'].append(lv['text']['dark_time'])
      jdata['night-obj'].append(jdata['text-obj'][-1])
    else:
      jdata['night-prb'].append(None)
      jdata['night-sec'].append(None)
      jdata['night-obj'].append(None)

    chance = lv['types_chances'].get('siluet')
    if chance:
      jdata['sil-prb'].append(chance)
      jdata['sil-sec'].append(jdata['text-sec'][-1])
      jdata['sil-obj'].append(jdata['text-obj'][-1])
    else:
      jdata['sil-prb'].append(None)
      jdata['sil-sec'].append(None)
      jdata['sil-obj'].append(None)

    chance = lv['types_chances'].get('part')
    if chance:
      jdata['part-prb'].append(chance)
      jdata['part-sec'].append(lv['parts']['time'])
      jdata['part-obj'].append([
        lv['parts']['parts_num'],
        lv['parts']['part_easy'] + lv['parts']['part_normal'] + lv['parts']['part_hard']
        ])
    else:
      jdata['part-prb'].append(None)
      jdata['part-sec'].append(None)
      jdata['part-obj'].append(None)

    chance = lv['types_chances'].get('morph')
    if chance:
      jdata['morph-prb'].append(chance)
      jdata['morph-sec'].append(lv['morphs']['time'])
      jdata['morph-obj'].append(lv['morphs']['morph_easy'] + lv['morphs']['morph_normal'] + lv['morphs']['morph_hard'])
    else:
      jdata['morph-prb'].append(None)
      jdata['morph-sec'].append(None)
      jdata['morph-obj'].append(None)

    chance = lv['types_chances'].get('couple')
    if chance:
      jdata['pair-prb'].append(chance)
      jdata['pair-sec'].append(lv['couples']['time'])
      num = lv['couples']['couples_easy'] + lv['couples']['couples_normal'] + lv['couples']['couples_hard'] + lv['couples']['couples_very_easy'] + lv['couples']['couples_very_hard']
      jdata['pair-obj'].append([num, 2])
    else:
      jdata['pair-prb'].append(None)
      jdata['pair-sec'].append(None)
      jdata['pair-obj'].append(None)

    jdata['anom-sec'].append(lv['phenomen']['time'])
    jdata['anom-obj'].append(jdata['text-obj'][-1])

  def encode_image(imgpath):
    with open(os.path.join(imgdir, imgpath), 'r') as fh:
      return 'data:image/png;base64,' + base64.b64encode(fh.read())

  # 通常モードオブジェクト
  jdata['forms'] = []
  for obj in sceneobj['norm']:
    name = obj.pop(0)
    sceneid = name.split('.', 1)[0]

    sil = obj.pop(0)
    try:
      silimg = encode_image('{0}.sils/{1}.png'.format(sceneid, sil))
    except:
      silimg = encode_image('{0}.sils/{1}.png'.format(sceneid, name.split('.', 1)[1]))
    
    (norm, w, h) = obj.pop(0)
    try:
      normimg = encode_image('{0}.form/{1}.png'.format(sceneid, norm))
    except:
      normimg = encode_image('{0}.form/{1}.png'.format(sceneid, norm.lower()))

    if w > h:
      w = 85
      h = None
    else:
      h = 90
      w = None

    jdata['forms'].append({
      'name': textinfo[name].decode('utf-8'),
      'sil': silimg,
      'img': normimg,
      'w': w,
      'h': h})

  # かけらモードオブジェクト
  jdata['part'] = []
  for obj in sceneobj['part']:
    part = []
    for name in obj:
      try:
        part.append(encode_image('{0}.part/{1}.png'.format(sceneid, name)))
      except:
        try:
          part.append(encode_image('{0}.part/{1}.png'.format(sceneid, name.replace('_', ''))))
        except:
          part.append(encode_image('{0}.part/{1}.png'.format(sceneid, re.sub(r'_(?=\d$)', '', name))))

    jdata['part'].append(part)

  # モーフモードオブジェクト
  jdata['morph'] = []
  for obj in sceneobj['morph']:
    morph = []
    for (name, w, h) in obj:
      path = encode_image('{0}.morph/{1}.png'.format(sceneid, name))
      if w > h:
        w = 85
        h = None
      else:
        w = None
        h = 90

      morph.append({'img': path, 'w': w, 'h': h})

    jdata['morph'].append(morph)

  with open(os.path.join(dstdir, 'scene_{0}_prm.json'.format(scene['id'])), 'w') as fh:
    fh.write(json.dumps(jdata, indent=2, ensure_ascii=False).encode('utf-8'))


def main():
  try:
    (resdir, imgdir, dstdir, lang) = sys.argv[1:]
  except StandardError:
    sys.stderr.write('Usage: {0} resdir imgdir dstdir lang\n'.format(sys.argv[0]))
    sys.exit(2)

  textinfo = load_textfile(resdir, lang)

  sceneinfo = load_sceneinfo(resdir)

  scenelist = []
  for (id_, scene) in sorted(sceneinfo.items()):
    scene['id'] = id_
    scene['name'] = textinfo['IDS_SCENE_NAME_{0}'.format(id_)].decode('utf-8')[1:-1]
    scene['html'] = 'scene_{0}.html'.format(id_)

    if len(scenelist):
      scenelist[-1]['next'] = scene['html']
      scene['prev'] = scenelist[-1]['html']

    scenelist.append(scene)

  write_index(scenelist, dstdir)

  for scene in scenelist:
    sys.stderr.write('{0}: {1}\n'.format(scene['id'], scene['name'].encode('utf-8')))
    sceneobj = load_sceneobj(resdir, scene['xml'])

    #sys.stderr.write(json.dumps(scene, indent=2, ensure_ascii=False).encode('utf-8'))
    write_json(scene, sceneobj, textinfo, imgdir, dstdir)


if __name__ == '__main__':
  main()
