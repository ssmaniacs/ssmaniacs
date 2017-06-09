#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ts=2 et
'''Create multilingual scene_info.xx.json'''
import sys
import os
import glob
import json

def extract_langdata(fpath, langdata):
  info = {}

  with open(fpath, 'r') as fh:
    for line in fh:
      if ':' in line:
        (key, val) = line.split(':', 1)
        if key.startswith('IDS_SCENE_') or \
          key.startswith('IDS_ITEM_NAME_') or \
          (key in langdata['objects'].keys()):
          info[key.strip()] = val.strip().decode('utf-8')

  if not info:
    return False

  langdata['modes'] = {
    'text': info['IDS_SCENE_TYPE_0'],
    'night': info['IDS_SCENE_TYPE_1'],
    'silhouette': info['IDS_SCENE_TYPE_2'],
    'part': info['IDS_SCENE_TYPE_6'],
    'morph': info['IDS_SCENE_TYPE_8'],
    'pair': info['IDS_SCENE_TYPE_10'],
  }

  langdata['levels'] = [
    info['IDS_SCENE_STAGE_{0}'.format(n)] for n in range(0, 9)
  ]

  for key in langdata['scenes'].keys():
    langdata['scenes'][key] = info['IDS_SCENE_NAME_{0}'.format(key)][1:-1]

  for key in langdata['objects'].keys():
    langdata['objects'][key] = info[key]

  for key in langdata['items'].keys():
    langdata['items'][key] = info['IDS_ITEM_NAME_{0}'.format(key)]

  return True


def main():
  try:
    (resdir, datadir, dstdir) = sys.argv[1:]
  except:
    sys.stderr.write('Usage: {0} resdir datadir dstdir\n'.format(sys.argv[0]))
    sys.exit(2)

  langdata = {
    'scenes': {},
    'objects': {},
    'items': {},
  }

  # 作成済みデータJSONから抽出の必要な項目のIDを読み込む
  for fname in glob.glob(os.path.join(datadir, 'scene_*_data.json')):
    sys.stderr.write('Reading {0}\n'.format(fname))

    with open(fname, 'r') as fh:
      jdata = json.load(fh)

    # シーンID
    langdata['scenes'][jdata['id']] = None

    # 探索に必要なアイテム
    if jdata['levels'][0]['params'].get('firefly'):
      langdata['items'][jdata['levels'][0]['params']['fireflyId']] = None

    # オブジェクトID
    prefix = jdata['name'] + '.'

    for obj in jdata['images']['objects']['form']:
      langdata['objects'][(prefix + obj['name']).encode('utf-8')] = None

  # 言語ファイルからしてされた項目のテキストを取得する
  for fpath in glob.glob(os.path.join(resdir, '1024', 'properties', 'default*.xml')):
    fname = os.path.basename(fpath)

    if fname == 'default.xml':
      lang = 'en'
    else:
      lang = fname.rsplit('.', 1)[0].rsplit('_', 1)[1]

    if not extract_langdata(fpath, langdata):
      continue

    outname = os.path.join(dstdir, 'scene_info.{0}.json'.format(lang))
    with open(outname, 'w') as fh:
      print 'Generating {0}'.format(outname)
      fh.write(json.dumps(langdata, indent=2, sort_keys=True, ensure_ascii=False).encode('utf-8'))

if __name__ == '__main__':
  main()
