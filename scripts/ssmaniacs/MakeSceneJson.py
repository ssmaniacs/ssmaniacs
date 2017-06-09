#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ts=2 et
'''
- SceneParam、ObjectFinder用JSONファイルを作成
'''

import sys
import os
import glob
import json
import base64
from collections import OrderedDict

# 画像合成時の固定オフセット
# SS定義ファイルが左上座標を (-228, 0) として記述されている。
XOFFSET = 228
YOFFSET = 0


def encode_img(path):
  with open(path, 'rb') as fh:
    return 'data:image/png;base64,' + base64.b64encode(fh.read())


def output_bg(scene, imgdir, template, outdir, embed):
  '''シーンバックグラウンド情報をJSONに出力'''
  outpath = os.path.join(outdir, 'scene_{0}_bg{1}.json'.format(scene['id'], ('' if embed else 'p')))
  sys.stderr.write('Generating {0}\n'.format(outpath))

  bginfo = []

  for (layer, images) in sorted(scene['images']['background'].items()):
    for srcimg in images:
      dstimg = {
        'layer': int(layer),
      }
      if srcimg.get('ani'):
        if srcimg['frame'] != 0:  # 最初のフレームの情報のみ格納
          continue

        # フレーム画像は img.path の画像の (frame.x,frame.y)-(frame.x+frame.w,frame.y+frame.h)
        # アニメフレームの描画座標は scene_*.xml の (pic.x+228-frame.fregx), (pic.y-frame.fregy)
        dstimg['path'] = srcimg['conv']
        #sys.stderr.write('ANI {0} => {1}\n'.format(srcimg['name'], dstimg['path']))

        dstimg['x'] = srcimg['x'] - srcimg['regx'] + XOFFSET
        dstimg['y'] = srcimg['y'] - srcimg['regy'] + YOFFSET
        dstimg['ani'] = True
      else:
        dstimg['path'] = srcimg['conv']
        #sys.stderr.write('PNG {0} => {1}\n'.format(srcimg['orig'], dstimg['path']))

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


  with open(outpath, 'w') as fh:
    json.dump(bginfo, fh, indent=2, sort_keys=True)


def output_obj(scene, imgdir, outdir, embed):
  '''シーンバックグラウンド情報をJSONに出力'''
  outpath = os.path.join(outdir, 'scene_{0}_obj{1}.json'.format(scene['id'], ('' if embed else 'p')))
  sys.stderr.write('Generating {0}\n'.format(outpath))

  # オブジェクトイメージ情報を格納
  objinfo = {
    'form': [],
    'part': [],
    'morph': []
  }

  def copy_imgitem(img, type):
    dst = {}
    #dst['name'] = img['name']
    dst['path'] = img['conv']
    dst['x'] = img['x'] + XOFFSET
    dst['y'] = img['y'] + YOFFSET
    dst['w'] = img['w']
    dst['h'] = img['h']
    dst['layer'] = img['layer']
    if embed:
      dst['data'] = encode_img(os.path.join(imgdir, dst['path']))
    return dst

  for form in scene['images']['objects']['form']:
    obj = {}
    obj['name'] = scene['name'] + '.' + form['name']
    obj['path'] = form['conv']
    if embed:
      obj['data'] = encode_img(os.path.join(imgdir, obj['path']))
    obj['images'] = []

    for item in form['images']:
      obj1 = {}
      for (tag, img) in item.items():
        obj1[tag] = copy_imgitem(img, 'form')

      obj['images'].append(obj1)

    objinfo['form'].append(obj)


  for part in scene['images']['objects']['part']:
    obj = {}
    #obj['name'] = part['name']
    obj['path'] = part['conv']
    if embed:
      obj['data'] = encode_img(os.path.join(imgdir, obj['path']))
    obj['pieces'] = []

    for piece in part['pieces']:
      obj1 = {}
      #obj1['name'] = piece['name']
      obj1['path'] = piece['conv']
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

  for morph in scene['images']['objects']['morph']:
    obj = {}
    #obj['name'] = morph['name']
    obj['images'] = []

    for item in morph['images']:
      obj1 = {}
      for (tag, img) in item.items():
        obj1[tag] = copy_imgitem(img, 'morph')

      obj['images'].append(obj1)

    objinfo['morph'].append(obj)


  with open(outpath, 'w') as fh:
    fh.write(json.dumps(objinfo, indent=2, sort_keys=True))


def output_prm(scene, imgdir, outdir, embed):
  '''シーン情報JSONを書き出す'''
  outpath = os.path.join(outdir, 'scene_{0}_prm.json'.format(scene['id']))
  sys.stderr.write('Generating {0}\n'.format(outpath))

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
      jdata['charge'].append({'item': p['fireflyId'], 'count': ff})
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

  # 通常モードオブジェクト
  jdata['forms'] = []
  for obj in scene['images']['objects']['form']:
    pic = obj['images'][0]['pic']
    if pic['w'] > pic['h']:
      w = 85
      h = None
    else:
      h = 90
      w = None

    if embed:
      sil = encode_img(os.path.join(imgdir, obj['conv']))
      img = encode_img(os.path.join(imgdir, pic['conv']))
    else:
      sil = obj['conv']
      img = pic['conv']

    jdata['forms'].append({
      'name': obj['name'],
      'sil': sil,
      'img': img,
      'w': w,
      'h': h})

  # かけらモードオブジェクト
  jdata['part'] = []
  for obj in scene['images']['objects']['part']:
    paths = [obj['conv']] + [p['conv'] for p in obj['pieces']]
    if embed:
      paths = [encode_img(os.path.join(imgdir, p)) for p in paths]

    jdata['part'].append(paths)

  # モーフモードオブジェクト
  jdata['morph'] = []
  for obj in scene['images']['objects']['morph']:
    morph = []
    img = obj['images'][0]
    for pic in (img['pic1'], img['pic2']):
      if pic['w'] > pic['h']:
        w = 85
        h = None
      else:
        w = None
        h = 90

      if embed:
        img = encode_img(os.path.join(imgdir, pic['conv']))
      else:
        img = pic['conv']

      morph.append({'img': img, 'w': w, 'h': h})

    jdata['morph'].append(morph)


  with open(outpath, 'w') as fh:
    fh.write(json.dumps(jdata, indent=2, ensure_ascii=False).encode('utf-8'))


def main():
  if len(sys.argv) < 4:
    sys.stderr.write('Usage: {0} imgdir outdir {{bg|obj|prm|embed}}[...] scene_*_data.json [...]\n'.format(sys.argv[0]))
    sys.exit(2)

  (imgdir, outdir) = sys.argv[1:3]

  embed = False
  outputs = []
  targets = []
  for arg in sys.argv[3:]:
    if os.path.isfile(arg):
      targets.append(arg)
    elif arg == 'embed':
      embed = True
    else:
      outputs.append(arg)

  if 'bg' in outputs:
    with open('scene_template.json', 'r') as fh:
      template = json.load(fh)

  # 各シーン情報を処理する
  for fname in targets:
    with open(fname, 'r') as fh:
      scene = json.load(fh)

    sys.stderr.write('Processing: {0} ({1})\n'.format(fname, scene['name']))

    if 'bg' in outputs:
      output_bg(scene, imgdir, template.get(str(scene['id']), {}), outdir, embed)

    if 'obj' in outputs:
      output_obj(scene, imgdir, outdir, embed)

    if 'prm' in outputs:
      output_prm(scene, imgdir, outdir, embed)


if __name__ == '__main__':
  main()
