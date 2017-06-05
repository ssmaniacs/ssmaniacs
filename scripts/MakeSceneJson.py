#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ts=2 et
'''
各シーンのイメージ（背景、オブジェクト）を合成する
- レイヤ別のイメージJPG・マスクJPGとなっているものを透過PNGに変換
- アニメーション用イメージをフレームごとに分割
- ObjectFinder用JSONファイルを作成

INPUT:
- 1024/properties/data_scenes.xml
    シーン内部名、パラメータXMLファイルパスなど

- 1024/levles/scene_<ID>.xml
    イメージ情報（内部名、イメージパス、サイズなど

- 1024/images/levels/ho_chapter1/<scene-name>/
'''

import sys
import os
import glob
import json
import base64
from xml.etree import ElementTree
from collections import OrderedDict

# 背景画像全体のサイズ
BG_WIDTH = 1480
BG_HEIGHT = 690

# 画像合成時の固定オフセット
# SS定義ファイルが左上座標を (-228, 0) として記述されている。
XOFFSET = 228
YOFFSET = 0


def load_textinfo(resdir, lang):
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

  return textinfo


def load_scenelist(resdir):
  '''シーンパラメータリストを読み込む'''
  scenelist = {}

  root = ElementTree.parse(os.path.join(resdir, '1024',
    'properties', 'data_scenes.xml')).getroot()

  for scene in root.findall('scene'):
    id_ = int(scene.get('id'))
    scenelist[id_] = {
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

    scenelist[id_]['levels'] = lvlist

  return scenelist


def clickzones(scene, obj):
  '''クリックオブジェクト情報読み込み'''
  zonelist = []

  for zone in obj:
    image = OrderedDict()

    for item in zone:
      if item.tag in image:
        sys.stderr.write('Duplicate tag {0} in scene {1} {2}\n'.format(item.tag, scene, obj.get('name')))
        continue

      try:
        for key in item.attrib.keys():
          if key not in ('name', 'texture', 'w', 'h', 'x', 'y', 'layer'):
            raise RuntimeError('Unexpected attribute\n{0}'.format(str(item.attrib)))

        attr = OrderedDict()

        name = item.attrib['name'].split('.')

        if name[0] == scene:
          del name[0]

        if name[-1] in 'pic':
          del name[-1]

        attr['name'] = '.'.join(name)
        attr['path'] = item.attrib['texture']

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


def load_sceneimg(resdir, xmlpath):
  '''シーンの画像定義を読み込む'''
  root = ElementTree.parse(os.path.join(resdir, '1024', xmlpath)).getroot()
  info = OrderedDict()

  # シーン名ID
  info['name'] = root.get('name')

  # 背景画像
  info['background'] = OrderedDict()

  for pic in root.find('scene_pics'):
    if not pic.attrib['visible'] or not pic.attrib['texture']:
      continue  # 非描画指定およびイメージパス未指定

    # イメージ内部名を取得
    name = pic.attrib['name'].split('.')
    if name[0] == info['name']:     # 先頭部分はシーン名と同じはずなので除外
      del name[0]

    if name[-1] in ('pic', 'ani', 'xml'):
      del name[-1]


    layer = int(pic.attrib['layer'])

    if layer not in info['background']:
      info['background'][layer] = []

    if pic.get('ani'):
      # アニメーション定義を読み込み
      try:
        aniroot = ElementTree.parse(os.path.join(
          resdir, '1024', pic.attrib['texture'])).getroot()
      except ElementTree.ParseError:
        # special case
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
      '''
<animsprite>
  <img path="images/levels/ho_chapter1/india/bg/anim/smoke/smoke"   regx="35" regy="83" name="f" w="0" h="0"/>
  <framelist>
    <frame regx="29" regy="36" name="00.png" w="58" h="73" x="233" y="240"/>
    ...
      '''
      # フレーム画像は img.path の画像の (frame.x,frame.y)-(frame.x+frame.w,frame.y+frame.h)
      # フレームの描画座標は scene_*.xml の (pic.x+228-frame.fregx), (pic.y-frame.fregy)
      anipath = aniroot.find('img').get('path')

      # イメージファイル名を内部名とする
      name = pic.attrib['texture'].rsplit('/', 1)[-1].split('.')
      if name[0] == info['name']:     # 先頭部分がシーン名と同じなら除外
        del name[0]

      if name[-1] in ('pic', 'ani', 'xml', 'jpg', 'png'):
        del name[-1]

      frames = set()
      frmidx = 0
      for frm in aniroot.findall('framelist/frame'):
        key = '.'.join([frm.get('x', ''), frm.get('y', ''), frm.get('w', ''), frm.get('h', '')])
        if key in frames: # 回転アニメの場など、合同一座標のフレームが存在する
          continue
        if frm.get('w', '0') == '0' or frm.get('h', '0') == '0': # 幅・高さいずれかが0
          continue

        frames.add(key)

        fname = frm.attrib['name'].split('.')
        if fname[-1] == 'png':
          del fname[-1]

        frminfo = OrderedDict()
        frminfo['type'] = 'ani'

        n1 = []
        for n in name:
          n1 += n.split('_')

        n2 = []
        for n in fname:
          n2 += n.split('_')

        n3 = []
        while n1 and n2:
          if n1[0] == n2[0]:
            n3.append(n1.pop(0))
            del n2[0]
          else:
            break

        frminfo['name'] = '.'.join(['_'.join(name), '_'.join(n3 + n1 + n2)])
        #sys.stderr.write('name: {0}\n'.format(name))
        #sys.stderr.write('fname: {0}\n'.format(fname))
        #sys.stderr.write('->: {0} {1} {2}\n'.format(n3, n1, n2))
        #sys.stderr.write('->: {0}\n'.format(frminfo['name']))

        frminfo['path'] = anipath

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
      picinfo['name'] = '.'.join(name)
      picinfo['path'] = pic.attrib['texture']

      for key in ('x', 'y', 'centerx', 'centery', 'alpha', 'ani'):
        if key in pic.attrib:
          picinfo[key] = int(pic.attrib[key])

      info['background'][layer].append(picinfo)


  # 探索オブジェクト
  info['objects'] = OrderedDict()

  for objtype in root.findall('objects/*'):
    # 通常モード（文字、シルエット、夜、ペア)
    if objtype.tag == 'standart':
      info['objects']['form'] = []

      for obj in objtype.findall('gray_object'):
        objinfo = OrderedDict()

        name = obj.get('list_name')
        if name.startswith(info['name'] + '.'):
          name = name.split('.', 1)[1]

        objinfo['name'] = name
        objinfo['silpath'] = obj.get('list_sil')
        objinfo['images'] = clickzones(info['name'], obj)

        info['objects']['form'].append(objinfo)

    # かけらモード
    elif objtype.tag == 'part':
      info['objects']['part'] = []

      for part in objtype.findall('part_object'):
        objinfo = OrderedDict()

        path = part.get('image')
        objinfo['name'] = path.rsplit('/', 1)[-1] # name の明示的な定義はない
        objinfo['allpath'] = path
        objinfo['pieces'] = []

        for obj in part.findall('gray_object'):
          partinfo = OrderedDict()

          name = obj.get('name').split('.')

          if name[0] == info['name']:
            del name[0]

          if name[-1] == 'gobj':
            del name[-1]

          partinfo['name'] = '.'.join(name)
          partinfo['path'] = obj.get('list_part')
          partinfo['images'] = clickzones(info['name'], obj)

          objinfo['pieces'].append(partinfo)

        info['objects']['part'].append(objinfo)

    # モーフモード
    elif objtype.tag == 'morph':
      info['objects']['morph'] = []

      for obj in objtype.findall('gray_object'):
        objinfo = OrderedDict()

        name = obj.get('name').split('.')

        if name[0] == info['name']:
          del name[0]

        if name[-1] == 'gobj':
          del name[-1]

        objinfo['name'] = '.'.join(name)
        objinfo['images'] = clickzones(info['name'], obj)

        info['objects']['morph'].append(objinfo)

  return info


def convert_list(scene, resdir, imgdir):
  '''イメージ変換用リストを作成(シェルスクリプトへの入力)'''

  def find_files(path, name):
    '''イメージファイルおよびマスクファイル実体を見つける'''
    exact = False
    fullpath = os.path.join(resdir, '1024', path)
    for fore in glob.glob(fullpath + '.*'):
      if fore[-4:] in ('.png', '.jpg'):
        exact = True  # 一致するファイルが見つかった
        break
    else:
      # たまに微妙なスペルのブレがある（アンダーバー有無、複数形s有無など)
      sys.stderr.write('{0}.* not found\n'.format(path))

      fullpath = fullpath.rsplit('/', 1)[0] + '/' + name.rsplit('.', 1)[-1]
      for fore in glob.glob(fullpath + '.*'):
        if fore[-4:] in ('.png', '.jpg'):
          sys.stderr.write('=> {0} found instead\n'.format(fore[len(resdir)+6:]))
          break
      else:
        if '/covers/' in path:
          fullpath = os.path.join(resdir, '1024', path).replace('/covers/', '/cover/')
          for fore in glob.glob(fullpath + '.*'):
            if fore[-4:] in ('.png', '.jpg'):
              sys.stderr.write('=> {0} found instead\n'.format(fore[len(resdir)+6:]))
              break
          else:
            return (None, None)
        else:
          return (None, None)

    for mask in glob.glob(fore[:-4] + '_.*'):
      if mask[-4:] == fore[-4:]:
        if not exact:
          sys.stderr.write('=> {0} found instead\n'.format(mask[len(resdir)+6:]))
        break
    else:
      mask = None

    return (fore, mask if mask else '-')

  def output_combine(fore, mask, name, tag):
    '''コンバインリストを出力する'''
    dest = os.path.join(imgdir, scene['name'] + '.' + tag, name + '.png')
    present = os.path.isfile(dest)

    print 'COMBINE\t{0}\t{1}\t{2}{3}'.format(
      fore.replace('\\', '/'),
      mask.replace('\\', '/'),
      dest.replace('\\', '/'),
      '\tEXISTS' if present else '')

  def output_crop(sname, dname, x, y, w, h, tag):
    '''切り出しリストを出力する'''
    sfile = os.path.join(imgdir, scene['name'] + '.' + tag, sname + '.png')
    dfile = os.path.join(imgdir, scene['name'] + '.' + tag, dname + '.png')
    present = os.path.isfile(dfile)

    print 'CROP\t{0}\t{1}\t{2}{3}'.format(
      sfile.replace('\\', '/'),
      '{0}x{1}{2:+d}{3:+d}'.format(int(w), int(h), int(x), int(y)),
      dfile.replace('\\', '/'),
      '\tEXISTS' if present else '')

  combined = set()

  for bg in scene['background'].values():
    for img in bg:
      if img['type'] == 'ani':
        (name, aname) = img['name'].split('.', 1)
      else:
        name = img['path'].rsplit('/', 1)[-1]

      if img['path'] not in combined:
        combined.add(img['path'])
        (fore, mask) = find_files(img['path'], name)
        if fore:
          output_combine(fore, mask, name, 'bg')
        else:
          print '# {0}: {1} {2} image not found'.format(scene['name'], img['name'], img['path'])

      if img['type'] == 'ani':
        output_crop(name, aname, img['cropx'], img['cropy'], img['cropw'], img['croph'], 'bg')

  for form in scene['objects']['form']:
    (fore, mask) = find_files(form['silpath'], form['name'])
    if fore:
      output_combine(fore, mask, form['name'], 'sils')
    else:
      print '# {0} image not found'.format(form['silpath'])

    for item in form['images']:
      for img in item.values():
        (fore, mask) = find_files(img['path'], img['name'])
        if fore:
          output_combine(fore, mask, img['name'], 'form')
        else:
          print '# {0} image not found'.format(img['path'])

  for part in scene['objects']['part']:
    (fore, mask) = find_files(part['allpath'], part['name'])
    if fore:
      output_combine(fore, mask, part['name'], 'part')
    else:
      print '# {0} image not found'.format(part['allpath'])

    for piece in part['pieces']:
      (fore, mask) = find_files(piece['path'], piece['name'])
      if fore:
        output_combine(fore, mask, piece['name'], 'part')
      else:
        print '# {0} image not found'.format(piece['path'])

      for item in piece['images']:
        for img in item.values():
          (fore, mask) = find_files(img['path'], img['name'])
          if fore:
            output_combine(fore, mask, img['name'], 'part')
          else:
            print '# {0} image not found'.format(img['path'])

  for morph in scene['objects']['morph']:
    for item in morph['images']:
      for img in item.values():
        (fore, mask) = find_files(img['path'], img['name'])
        if fore:
          output_combine(fore, mask, img['name'], 'morph')
        else:
          print '# {0} image not found'.format(img['path'])


def encode_img(path):
  with open(path, 'rb') as fh:
    return 'data:image/png;base64,' + base64.b64encode(fh.read())


def output_bg(sceneid, sceneimg, imgdir, template, embed):
  '''シーンバックグラウンド情報をJSONに出力'''
  # シーン内部名
  scene = sceneimg['name']

  # バックグラウンドイメージ情報をレイヤ順に格納
  bginfo = []

  for (layer, images) in sorted(sceneimg['background'].items()):
    for srcimg in images:
      dstimg = {
        'layer': layer,
      }
      if srcimg.get('ani'):
        if srcimg['frame'] != 0:  # 最初のフレームの情報のみ格納
          continue

        # フレーム画像は img.path の画像の (frame.x,frame.y)-(frame.x+frame.w,frame.y+frame.h)
        # アニメフレームの描画座標は scene_*.xml の (pic.x+228-frame.fregx), (pic.y-frame.fregy)
        dstimg['path'] = (scene + '.bg/' + srcimg['name'].split('.')[-1] + '.png').replace('\\', '/')
        dstimg['x'] = srcimg['x'] - srcimg['regx'] + XOFFSET
        dstimg['y'] = srcimg['y'] - srcimg['regy'] + YOFFSET
        dstimg['ani'] = True
      else:
        # dstimg['path'] = (scene + '.bg/' + srcimg['name'] + '.png').replace('\\', '/')
        # 同じイメージファイルを異なるイメージ名で使いまわすことがあるので
        # 元ファイル名を使用する
        dstimg['path'] = (scene + '.bg/' + srcimg['path'].rsplit('/', 1)[-1] + '.png').replace('\\', '/')
        dstimg['x'] = srcimg['x'] - srcimg.get('centerx', 0) + XOFFSET
        dstimg['y'] = srcimg['y'] - srcimg.get('centery', 0) + YOFFSET

      imgpath = os.path.join(imgdir, dstimg['path'])
      if not os.path.isfile(imgpath):
        sys.stderr.write('Image file {0} does not exist\n'.format(imgpath))
        continue

      if embed:
        dstimg['data'] = encode_img(imgpath)

      for tmpl in template.get('background', []):
        if dstimg['path'] == tmpl['path'] and dstimg['x'] == tmpl['x'] and dstimg['y'] == tmpl['y']:
          if 'type' in tmpl:
            dstimg['type'] = tmpl['type']
          tmpl['present'] = True
          break
      else:
        sys.stderr.write('{0} (x:{1},y{2}) not present in template\n'.format(
          dstimg['path'], dstimg['x'], dstimg['y']))

      bginfo.append(dstimg)

  for tmpl in template.get('background', []):
    if 'present' not in tmpl:
      sys.stderr.write('{0} (x:{1},y{2}) only present in template\n'.format(
        tmpl['path'], tmpl['x'], tmpl['y']))

  with open('scene_{0}_bg.json'.format(sceneid), 'w') as fh:
    json.dump(bginfo, fh, indent=2, sort_keys=True)


def output_obj(sceneid, sceneimg, imgdir, textinfo, embed):
  '''シーンバックグラウンド情報をJSONに出力'''
  # オブジェクトイメージ情報を格納
  objinfo = {
    'form': [],
    'part': [],
    'morph': []
  }

  scene = sceneimg['name']

  def adjust_path(tag, name):
    path = '/'.join([scene + '.' + tag, name + '.png'])
    if not os.path.isfile(os.path.join(imgdir, path)):
      raise RuntimeError('{0} not exists\n'.format(path))
    return path

  def copy_imgitem(img, type):
    dst = {}
    dst['name'] = img['name']
    dst['path'] = adjust_path(type, img['name'])
    dst['x'] = img['x'] + XOFFSET
    dst['y'] = img['y'] + YOFFSET
    dst['w'] = img['w']
    dst['h'] = img['h']
    dst['layer'] = img['layer']
    if embed:
      dst['data'] = encode_img(os.path.join(imgdir, dst['path']))
    return dst

  for form in sceneimg['objects']['form']:
    obj = {}
    obj['name'] = textinfo[scene + '.' + form['name']].decode('utf-8')
    obj['path'] = adjust_path('sils', form['name'])
    if embed:
      obj['data'] = encode_img(os.path.join(imgdir, obj['path']))
    obj['images'] = []

    for item in form['images']:
      obj1 = {}
      for (tag, img) in item.items():
        obj1[tag] = copy_imgitem(img, 'form')

      obj['images'].append(obj1)

    objinfo['form'].append(obj)


  for part in sceneimg['objects']['part']:
    obj = {}
    obj['name'] = part['name']
    obj['path'] = adjust_path('part', part['name'])
    if embed:
      obj['data'] = encode_img(os.path.join(imgdir, obj['path']))
    obj['pieces'] = []

    for piece in part['pieces']:
      obj1 = {}
      obj1['name'] = piece['name']
      obj1['path'] = adjust_path('part', piece['name'])
      if embed:
        obj1['data'] = encode_img(os.path.join(imgdir, obj1['path']))
      obj1['images'] = []

      for item in piece['images']:
        obj2 = {}
        for (tag, img) in item.items():
          obj2[tag] = copy_imgitem(img, 'part')

        obj1['images'].append(obj2)

      obj['pieces'].append(obj1)

    objinfo['part'].append(obj)

  for morph in sceneimg['objects']['morph']:
    obj = {}
    obj['name'] = morph['name']
    obj['images'] = []

    for item in morph['images']:
      obj1 = {}
      for (tag, img) in item.items():
        obj1[tag] = copy_imgitem(img, 'morph')

      obj['images'].append(obj1)

    objinfo['morph'].append(obj)


  with open('scene_{0}_obj.json'.format(sceneid), 'w') as fh:
    fh.write(json.dumps(objinfo, indent=2, sort_keys=True, ensure_ascii=False).encode('utf-8'))

def output_prm(scene, sceneimg, imgdir, textinfo, embed):
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

  scname = sceneimg['name']

  def adjust_path(tag, objname):
    path = '/'.join([scname + '.' + tag, objname + '.png'])
    if not os.path.isfile(os.path.join(imgdir, path)):
      raise RuntimeError('{0} not exists\n'.format(path))

    if embed:
      with open(os.path.join(imgdir, path), 'r') as fh:
        return 'data:image/png;base64,' + base64.b64encode(fh.read())
    else:
      return path

  # 通常モードオブジェクト
  jdata['forms'] = []
  for obj in sceneimg['objects']['form']:
    objname = obj['name']

    silimg = adjust_path('sils', objname)
    pic = obj['images'][0]['pic']
    normimg = adjust_path('form', pic['name'])
    if pic['w'] > pic['h']:
      w = 85
      h = None
    else:
      h = 90
      w = None

    jdata['forms'].append({
      'name': textinfo[scname + '.' + objname].decode('utf-8'),
      'sil': silimg,
      'img': normimg,
      'w': w,
      'h': h})

  # かけらモードオブジェクト
  jdata['part'] = []
  for obj in sceneimg['objects']['part']:
    parts = [adjust_path('part', obj['name'])]

    for piece in obj['pieces']:
      parts.append(adjust_path('part', piece['name']))

    jdata['part'].append(parts)

  # モーフモードオブジェクト
  jdata['morph'] = []
  for obj in sceneimg['objects']['morph']:
    morph = []
    img = obj['images'][0]
    for pic in (img['pic1'], img['pic2']):
      path = adjust_path('morph', pic['name'])
      if pic['w'] > pic['h']:
        w = 85
        h = None
      else:
        w = None
        h = 90

      morph.append({'img': path, 'w': w, 'h': h})

    jdata['morph'].append(morph)

  with open('scene_{0}_prm.json'.format(scene['id']), 'w') as fh:
    fh.write(json.dumps(jdata, indent=2, ensure_ascii=False).encode('utf-8'))


def output_list(scenelist, targets):
  '''シーンリストJSを出力する'''
  sclist = dict([(id, scenelist[id]['name']) for id in targets])

  with open('scene_idx.js', 'w') as fh:
    fh.write('var scene_list =\n')
    fh.write(json.dumps(sclist, indent=2, ensure_ascii=False).encode('utf-8'))
    fh.write(';\n')


def main():
  if len(sys.argv) < 5:
    sys.stderr.write('Usage: {0} resdir imgdir lang {{dump|conv|list|bg|obj|prm|embed}}[...] [sceneid ...]\n'.format(sys.argv[0]))
    sys.stderr.write('''
1. conv コマンドで変換リストを生成する
   $ ./{0} ... conv > convlist.tsv

2. convert_images.sh で変換を実施
   $ ./convert_images.sh convlist.tsv

3. obj prm bg コマンドでjson (イメージパス版) を出力する
   (scene_ID_bgp.json, scene_ID_objp.json)

4. ObjectFinder.htmlをパス版jsonで実行 (ObjectFinder.html?image_root=path&bg_control=true)

5. scene_template.jsonを適宜修正 ("type":"skip", "type":"effect" の追記など)

6. json-data コマンドでjson (イメージ埋め込み版) を出力する （または EmbedImageData.py)
   (scene_ID_bg.json, scene_ID_obj.json)
'''.format(sys.argv[0]))

    sys.exit(2)

  (resdir, imgdir, lang) = sys.argv[1:4]

  embed = False
  outputs = []
  targets = []
  for arg in sys.argv[4:]:
    try:
      targets.append(int(arg))
    except ValueError:
      if arg == 'embed':
        embed = True
      else:
        outputs.append(arg)

  # シーン一覧を読み込む
  scenelist = load_scenelist(resdir)

  if not targets:
    # 全てのシーンをターゲットとする
    targets = sorted(scenelist.keys())

  # 表示用テキスト情報を読み込む
  textinfo = load_textinfo(resdir, lang);

  if 'bg' in outputs:
    with open('scene_template.json', 'r') as fh:
      template = json.load(fh)

  # 各シーンのイメージ情報を読み込む
  for id in targets:
    scene = scenelist[id]

    scene['name'] = textinfo['IDS_SCENE_NAME_{0}'.format(id)].decode('utf-8')[1:-1]

    sys.stderr.write('Processing: {0} ({1})\n'.format(
      scene['xml'], scene['name'].encode('utf-8')))

    sceneimg = load_sceneimg(resdir, scene['xml'])

    if 'dump' in outputs:
      print json.dumps(sceneimg, indent=2)

    if 'conv' in outputs:
      # メイン画像・マスク画像合成用のリストを生成
      #   メイン.jpg<TAB>マスク.jpg<TAB>ターゲット.png
      #   メイン.png<TAB>-<TAB>ターゲット.png
      # ImageMagick convert で合成：
      #   convert メイン マスク \( -clone 0 -alpha extract \) ￥
      #     \( -clone 1 -clone 2 -compose multiply -composite \) \
      #     -delete 1,2 -alpha off -compose copy_opacity -composite ターゲット
      convert_list(sceneimg, resdir, imgdir)

    if 'bg' in outputs:
      sys.stderr.write('Generating background info\n')
      output_bg(id, sceneimg, imgdir, template.get(str(id), {}), embed)

    if 'obj' in outputs:
      sys.stderr.write('Generating object info\n')
      output_obj(id, sceneimg, imgdir, textinfo, embed)

    if 'prm' in outputs:
      sys.stderr.write('Generating parameter info\n')
      output_prm(scene, sceneimg, imgdir, textinfo, embed)

  if 'list' in outputs:
    output_list(scenelist, targets)


if __name__ == '__main__':
  main()
