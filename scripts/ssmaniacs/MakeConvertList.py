#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ts=2 et
'''
各シーンのイメージ（背景、オブジェクト）を合成するためのリストを生成
- レイヤ別のイメージJPG・マスクJPGとなっているものを透過PNGに変換
- アニメーション用イメージをフレームごとに分割
'''

import sys
import os
import glob
import json
import base64
from xml.etree import ElementTree
from collections import OrderedDict


def make_convlist(resdir, imgdir, scene):
  '''イメージ変換用リストを作成(シェルスクリプトへの入力)'''
  #   メイン.jpg<TAB>マスク.jpg<TAB>ターゲット.png
  #   メイン.png<TAB>-<TAB>ターゲット.png
  # ImageMagick convert で合成：
  #   convert メイン マスク \( -clone 0 -alpha extract \) ￥
  #     \( -clone 1 -clone 2 -compose multiply -composite \) \
  #     -delete 1,2 -alpha off -compose copy_opacity -composite ターゲット
  while resdir.endswith('/'):
    resdir = resdir[:-1]

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
      sys.stderr.write('[!]{0}.* not found\n'.format(path))

      fullpath = fullpath.rsplit('/', 1)[0] + '/' + name.rsplit('.', 1)[-1]
      for fore in glob.glob(fullpath + '.*'):
        if fore[-4:] in ('.png', '.jpg'):
          sys.stderr.write(' =>{0} found instead\n'.format(fore[len(resdir)+6:]))
          break
      else:
        if '/covers/' in path:  # Playgroundのデータがおかしい
          fullpath = os.path.join(resdir, '1024', path).replace('/covers/', '/cover/')
          for fore in glob.glob(fullpath + '.*'):
            if fore[-4:] in ('.png', '.jpg'):
              sys.stderr.write(' =>{0} found instead\n'.format(fore[len(resdir)+6:]))
              break
          else:
            return (None, None)
        else:
          return (None, None)

    for mask in glob.glob(fore[:-4] + '_.*'):
      if mask[-4:] == fore[-4:]:
        if not exact:
          sys.stderr.write(' =>{0} found instead\n'.format(mask[len(resdir)+6:]))
        mask = os.path.basename(mask)
        break
    else:
      mask = None

    return (fore, mask if mask else '-')

  def output_combine(fore, mask, dest):
    '''コンバインリストを出力する'''
    dpath = os.path.join(imgdir, dest)
    present = os.path.isfile(dpath)

    print 'COMBINE\t{0}\t{1}\t{2}{3}'.format(
      fore.replace('\\', '/'),
      mask.replace('\\', '/'),
      dpath.replace('\\', '/'),
      '\tEXISTS' if present else '')

  def output_crop(sname, dname, x, y, w, h):
    '''切り出しリストを出力する'''
    spath = os.path.join(imgdir, sname)
    dpath = os.path.join(imgdir, sname.rsplit('/', 1)[0], dname)
    present = os.path.isfile(dpath)

    print 'CROP\t{0}\t{1}\t{2}{3}'.format(
      spath.replace('\\', '/'),
      '{0}x{1}{2:+d}{3:+d}'.format(int(w), int(h), int(x), int(y)),
      os.path.basename(dpath),
      '\tEXISTS' if present else '')

  combined = set()

  for bg in scene['images']['background'].values():
    for img in bg:
      if img['type'] == 'ani':
        (name, aname) = img['name'].split('.', 1)
        frames = os.path.join(os.path.dirname(img['conv']), name + '.png')
      else:
        name = img['name']

      if img['orig'] not in combined:
        combined.add(img['orig'])
        (fore, mask) = find_files(img['orig'], name)
        if fore:
          if img['type'] == 'ani':
            output_combine(fore, mask, frames)
          else:
            output_combine(fore, mask, img['conv'])

      if img['type'] == 'ani':
        output_crop(frames, aname + '.png',
          img['cropx'], img['cropy'], img['cropw'], img['croph'])

  for form in scene['images']['objects']['form']:
    (fore, mask) = find_files(form['orig'], form['name'])
    if fore:
      output_combine(fore, mask, form['conv'])

    for item in form['images']:
      for img in item.values():
        (fore, mask) = find_files(img['orig'], img['name'])
        if fore:
          output_combine(fore, mask, img['conv'])

  for part in scene['images']['objects']['part']:
    (fore, mask) = find_files(part['orig'], part['name'])
    if fore:
      output_combine(fore, mask, part['conv'])

    for piece in part['pieces']:
      (fore, mask) = find_files(piece['orig'], piece['name'])
      if fore:
        output_combine(fore, mask, piece['conv'])

      for item in piece['images']:
        for img in item.values():
          (fore, mask) = find_files(img['orig'], img['name'])
          if fore:
            output_combine(fore, mask, img['conv'])

  for morph in scene['images']['objects']['morph']:
    for item in morph['images']:
      for img in item.values():
        (fore, mask) = find_files(img['orig'], img['name'])
        if fore:
          output_combine(fore, mask, img['conv'])


def main():
  if len(sys.argv) < 4:
    sys.stderr.write('Usage: {0} resdir imgdir json [...]\n'.format(sys.argv[0]))
    sys.exit(2)

  (resdir, imgdir) = sys.argv[1:3]

  for fname in sys.argv[3:]:
    with open(fname, 'r') as fh:
      jdata = json.load(fh)

    sys.stderr.write('Processing: {0} ({1})\n'.format(fname, jdata['name']))
    make_convlist(resdir, imgdir, jdata)


if __name__ == '__main__':
  main()
