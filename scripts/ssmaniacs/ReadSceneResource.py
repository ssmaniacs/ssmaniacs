#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ts=2 et
'''
各シーンのリソースを読み込み、SSManiacs独自JSONを生成
この独自JSONから以下の情報が生成される
- イメージ変換リスト
- ObjectFinder.html および SceneParams.html 用のシーン情報JSON

INPUT:
- 1024/properties/data_scenes.xml
    各シーンの内部名、レベルごとのパラメータ、イメージ定義ファイルパスなど

- 1024/levles/scene_<ID>.xml
    イメージ内部名、イメージパス、位置、サイズなど

- 1024/images/levels/ho_chapter1/<scene_name>/.../*.xml
    scene_<ID>.xml で指定されたアニメーション定義ファイル

OUTPUT:
- ./scene_<ID>_data.json

'''

import sys
import os
import json
from xml.etree import ElementTree
from collections import OrderedDict


def load_scenelist(resdir):
  '''シーンパラメータリストを読み込む'''
  scenelist = {}

  root = ElementTree.parse(os.path.join(resdir, '1024',
    'properties', 'data_scenes.xml')).getroot()

  for scene in root.findall('scene'):
    id = int(scene.get('id'))

    scenelist[id] = OrderedDict()
    scenelist[id]['id'] = id
    scenelist[id]['name'] = scene.get('name')
    scenelist[id]['xml'] = scene.get('xml')

    lvlist = []
    for lv in scene.findall('level'):
      level = OrderedDict()

      for name in ('params', 'phenomen', 'text', 'parts',
        'couples', 'morphs', 'allowed', 'types_chances'):
        level[name] = lv.find(name).attrib

        for k in level[name].keys():
          level[name][k] = int(level[name][k])

      lvlist.append(level)

    scenelist[id]['levels'] = lvlist

  return scenelist


def load_sceneimg(resdir, scene):
  '''シーンの画像定義を読み込む'''
  root = ElementTree.parse(os.path.join(resdir, '1024', scene['xml'])).getroot()
  info = OrderedDict()

  # シーン内部名
  scname = root.get('name')

  # 背景画像
  info['background'] = OrderedDict()

  def adjust_name(name):
    n = name.split('.')
    if n[0] == scname:     # 先頭部分はシーン名と同じはずなので除外
      del n[0]

    if n[-1] in ('pic', 'ani', 'xml', 'jpg', 'png', 'gobj'):
      del n[-1]

    if len(n) > 1:
      sys.stderr.write('Name: {0}\n'.format(name))
      sys.stderr.write(str(pic.attrib))
      sys.stderr.write('\n')
      raise

    return '.'.join(n)


  def adjust_path(tag, path):
    '''SS maniacs内部イメージパス'''
    return '/'.join([scname + '.' + tag, path.rsplit('/', 1)[-1] + '.png'])


  for pic in root.find('scene_pics'):
    if not pic.attrib['visible'] or not pic.attrib['texture']:
      continue  # 非描画指定およびイメージパス未指定

    layer = int(pic.attrib['layer'])

    if layer not in info['background']:
      info['background'][layer] = []

    if pic.get('ani'):
      # アニメーション定義を読み込み
      try:
        aniroot = ElementTree.parse(os.path.join(
          resdir, '1024', pic.attrib['texture'])).getroot()
      except ElementTree.ParseError:
        # special case: XMLファイル内にElementTreeが扱えない記述ミスがある
        if pic.attrib['texture'] == 'images/levels/ho_chapter1/alchemist_room/bg/anim/bubble.xml':
          lines = []
          with open(os.path.join(resdir, '1024', pic.attrib['texture']), 'r') as fh:
            for line in fh:
              if '<pause value="1700">' not in line:
                lines.append(line)
          aniroot = ElementTree.fromstringlist(lines)

        else:
          sys.stderr.write(pic.attrib['texture'] + '\n')
          raise

      except StandardError:
          sys.stderr.write(pic.attrib['texture'] + '\n')
          raise

      # フレーム画像は img.path の画像の (frame.x,frame.y)-(frame.x+frame.w,frame.y+frame.h)
      # フレームの描画座標は scene_*.xml の (pic.x+228-frame.fregx), (pic.y-frame.fregy)
      anipath = aniroot.find('img').get('path')

      # イメージファイル名を内部名とする
      name = adjust_name(pic.attrib['texture'].rsplit('/', 1)[-1])

      frames = set()
      frmidx = 0
      for frm in aniroot.findall('framelist/frame'):
        key = '.'.join([frm.get('x', ''), frm.get('y', ''), frm.get('w', ''), frm.get('h', '')])
        if key in frames: # 回転アニメの場など、同一座標のフレームが存在する
          continue
        if frm.get('w', '0') == '0' or frm.get('h', '0') == '0': # 幅・高さいずれかが0
          continue

        frames.add(key)

        fname = adjust_name(frm.attrib['name'])

        frminfo = OrderedDict()
        frminfo['type'] = 'ani'

        n1 = name.split('_')
        n2 = fname.split('_')

        n3 = []
        while n1 and n2:
          if n1[0] == n2[0]:
            n3.append(n1.pop(0))
            del n2[0]
          else:
            break

        frmname = '_'.join(n3 + n1 + n2)  # フレーム名
        frminfo['name'] = '.'.join([name, frmname])
        frminfo['orig'] = anipath
        frminfo['conv'] = (scname + '.bg/' + frmname + '.png')

        for key in ('x', 'y', 'centerx', 'centery', 'alpha', 'ani'):
          if key in pic.attrib:
            frminfo[key] = int(pic.attrib[key])

        frminfo['regx'] = int(frm.attrib['regx'])
        frminfo['regy'] = int(frm.attrib['regy'])
        frminfo['cropx'] = int(frm.attrib['x'])
        frminfo['cropy'] = int(frm.attrib['y'])
        frminfo['cropw'] = int(frm.attrib['w'])
        frminfo['croph'] = int(frm.attrib['h'])
        frminfo['frame'] = frmidx
        frmidx += 1

        info['background'][layer].append(frminfo)

    else: # 単独イメージ
      picinfo = OrderedDict()
      picinfo['type'] = 'pic'
      picinfo['name'] = adjust_name(pic.attrib['name'])

      picinfo['orig'] = pic.attrib['texture']
      # 同じイメージファイルを異なる内部名で使いまわすことがあるので
      # 変換先には内部名ではなく元ファイル名を使用する
      picinfo['conv'] = adjust_path('bg', picinfo['orig'])

      for key in ('x', 'y', 'centerx', 'centery', 'alpha', 'ani'):
        if key in pic.attrib:
          picinfo[key] = int(pic.attrib[key])

      info['background'][layer].append(picinfo)


  def clickzones(tag, obj):
    '''クリックオブジェクト情報読み込み'''
    zonelist = []

    for zone in obj:
      image = OrderedDict()

      for item in zone:
        if item.tag in image:
          sys.stderr.write('Duplicate tag {0} in scene {1} {2}\n'.format(
            item.tag, scname, obj.get('name')))
          continue

        try:
          for key in item.attrib.keys():
            if key not in ('name', 'texture', 'w', 'h', 'x', 'y', 'layer'):
              raise RuntimeError('Unexpected attribute\n{0}'.format(str(item.attrib)))

          attr = OrderedDict()

          name = adjust_name(item.attrib['name'])

          attr['name'] = name
          attr['orig'] = item.attrib['texture']
          attr['conv'] = adjust_path(tag, name)

          for key in ('layer', 'x', 'y', 'w', 'h'):
            if item.attrib[key] == '':
              attr[key] = None
            else:
              attr[key] = int(item.attrib[key])

        except StandardError:
          sys.stderr.write(json.dumps(item.attrib, indent=2, sort_keys=True))
          sys.stderr.write('\n')
          raise

        image[item.tag] = attr

      zonelist.append(image)

    return zonelist

  # 探索オブジェクト
  info['objects'] = OrderedDict()

  for objtype in root.findall('objects/*'):
    # 通常モード（文字、シルエット、夜、ペア)
    if objtype.tag == 'standart':
      info['objects']['form'] = []

      for obj in objtype.findall('gray_object'):
        objinfo = OrderedDict()

        name = obj.get('list_name')
        if name.startswith(scname + '.'):
          name = name.split('.', 1)[1]

        objinfo['name'] = name
        objinfo['orig'] = obj.get('list_sil')
        objinfo['conv'] = adjust_path('sils', objinfo['orig'])
        objinfo['images'] = clickzones('form', obj)

        info['objects']['form'].append(objinfo)

    # かけらモード
    elif objtype.tag == 'part':
      info['objects']['part'] = []

      for part in objtype.findall('part_object'):
        objinfo = OrderedDict()

        path = part.get('image')
        objinfo['name'] = path.rsplit('/', 1)[-1] # name の明示的な定義はない
        objinfo['orig'] = path
        objinfo['conv'] = adjust_path('part', objinfo['orig'])
        objinfo['pieces'] = []

        for obj in part.findall('gray_object'):
          partinfo = OrderedDict()

          name = adjust_name(obj.get('name'))

          partinfo['name'] = name
          partinfo['orig'] = obj.get('list_part')
          partinfo['conv'] = adjust_path('part', partinfo['orig'])
          partinfo['images'] = clickzones('part', obj)

          objinfo['pieces'].append(partinfo)

        info['objects']['part'].append(objinfo)

    # モーフモード
    elif objtype.tag == 'morph':
      info['objects']['morph'] = []

      for obj in objtype.findall('gray_object'):
        objinfo = OrderedDict()

        name = adjust_name(obj.get('name'))

        objinfo['name'] = name
        objinfo['images'] = clickzones('morph', obj)

        info['objects']['morph'].append(objinfo)


  scene['name'] = scname
  scene['images'] = info


def main():
  if len(sys.argv) < 2:
    sys.stderr.write('Usage: {0} resdir [sceneid ...]\n'.format(sys.argv[0]))
    sys.exit(2)

  resdir = sys.argv[1]

  targets = []
  for arg in sys.argv[2:]:
    targets.append(int(arg))

  # シーン一覧を読み込む
  scenelist = load_scenelist(resdir)

  if not targets:
    # 全てのシーンをターゲットとする
    targets = sorted(scenelist.keys())

  # 各シーンのイメージ情報を処理する
  for id in targets:
    scene = scenelist[id]

    sys.stderr.write('Processing: {0} ({1})\n'.format(
      scene['xml'], scene['name']))

    load_sceneimg(resdir, scene)

    with open('scene_{0}_data.json'.format(id), 'w') as fh:
      sys.stderr.write('Writing: scene_{0}_data.json\n'.format(id))
      fh.write(json.dumps(scene, indent=2))


if __name__ == '__main__':
  main()
