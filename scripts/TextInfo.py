#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ts=2 et
import sys
import os
import json

# 人物が初登場するときのメッセージ
# IDS_FIRST_INTRODUCTION_PERSON_<key>
# <key>とIDS_NPC_NAME_のIDが一致しない
INTRO_PERSON = {
  '2': 1,       #'ジョン·ドウ',
  '1': 3,       #'ヴィンセント',
  'ALFRED': 4,  #'アルフレッド',
  '0': 5,       #'ハワード',
  '3': 6,       #'メイ・Ｇ',
  '4': 7,       #'ロザリンド',
  '5': 8,       #'ゴースト',
  '6': 9,       #'ダニー',
  '8': 10,      #'ルイス',
  '7': 11,      #'マイケル',
  '9': 12,      #'アリス',
  '10': 13,     #'ステファン',
  '11': 14,     #'レイチェル',
  '12': 17,     #'ディートリッヒ',
  '13': 18,     #'ガブリエル'
}
'''
IDS_NPC_NAME_1:ジョン・ドウ
IDS_NPC_NAME_2:クリスティ
IDS_NPC_NAME_3:ビンセント
IDS_NPC_NAME_4:アルフレッド
IDS_NPC_NAME_5:ハワード
IDS_NPC_NAME_6:メイ・Ｇ
IDS_NPC_NAME_7:ロザリンド
IDS_NPC_NAME_8:幽霊
IDS_NPC_NAME_9:ダニー
IDS_NPC_NAME_10:ルイス
IDS_NPC_NAME_11:マイケル
IDS_NPC_NAME_12:アリス
IDS_NPC_NAME_13:ステファン
IDS_NPC_NAME_14:レイチェル・フォックス
IDS_NPC_NAME_15:ジャクリーヌ
IDS_NPC_NAME_16:記録保管係
IDS_NPC_NAME_17:ディートリッヒ
IDS_NPC_NAME_18:ゴールドスミス
'''


def load_textinfo(rootdir, lang):
  if lang in (None, '', 'en'):
    filename = 'default.xml'
  else:
    filename = 'default_' + lang + '.xml'

  path = os.path.join(rootdir, '1024', 'properties', filename)

  info = {}
  id_ = None

  with open(path, 'r') as fh:
    for line in fh:
      if line[0] in (' ', '\t'):
        text = line
      elif ':' in line:
        (id_, text) = line.split(':', 1)
      else:
        continue

      text = text.strip()
      if not text:
        continue

      text = text.replace('&nbsp;', ' ').replace('&cr;', '\\n')

      try:
        if id_.startswith('Diary.Pages.ID.'):
          key1 = 'DIARY'
          key2 = 'PAGE'
          idval = int(id_.rsplit('.', 1)[-1])

        elif id_ in ('IDS_COLLECTIONS', 'IDS_ARTIFACTS'):
          info[id_] = text.decode('utf-8')
          continue

        elif id_.startswith('IDS_'):
          keys = id_.split('_')

          if keys[1] == 'DAGGER':
            #IDS_DAGGER_LETTER_NOTIFY_DESCR
            #IDS_DAGGER_LETTER_NOTIFY_TITLE
            key1 = 'LETTER'
            key2 = keys[4]
            idval = 999 #'DAGGER'
            if key2 == 'DESCR':
              key2 = 'TEXT'

          elif keys[1] == 'DIARY' and keys[2] == 'LEFT':
            #IDS_DIARY_LEFT_TEXT_[0-9]+
            key1 = 'DIARY'
            key2 = 'LEFT'
            idval = int(keys[-1])

          elif keys[1] == 'FIRST':
            #IDS_FIRST_INTRODUCTION_PERSON_
            key1 = 'PERSON'
            key2 = 'INTRO'
            idval = INTRO_PERSON.get(keys[4], keys[4])

          elif keys[1] == 'NPC':
            #IDS_NPC_NAME_
            key1 = 'PERSON'
            key2 = 'NAME'
            idval = int(keys[3])

          elif keys[1] == 'LETTER':
            #IDS_LETTER_
            if keys[2] in ('TITLE', 'TITLE2'):
              key1 = 'DIARY'
              key2 = 'TITLE'
            else:
              key1 = keys[1]
              key2 = keys[2]

            idval = int(keys[3])

          elif keys[1] == 'PHENOMEN':
            key1 = keys[1]
            key2 = 'NAME'
            idval = int(keys[2])

          elif keys[1] == 'SCENE' and keys[2] == 'TYPE':
            key1 = 'SCENETYPE'
            key2 = 'NAME'
            try:
              idval = int(keys[3])
            except (ValueError, IndexError):
              continue

          elif keys[1] == 'SCENE' and keys[2] == 'STAGE':
            key1 = 'LEVEL'
            key2 = 'NAME'
            try:
              idval = int(keys[3])
            except (ValueError, IndexError):
              continue

          elif keys[1] == 'PUZZLE':
            key1 = keys[1]

            if keys[2] == 'NAME':
              key2 = keys[2]
              idval = int(keys[3])

            elif keys[2] in ('BLOCK', 'BLOCKS'):
              idval = 1
              if keys[3] == 'DESCRIPTION':
                key2 = 'DESC'
              else:
                key2 = 'TUTORIAL'

            elif keys[2] in ('MOSAIC'):
              idval = 2
              if keys[3] == 'DESCRIPTION':
                key2 = 'DESC'
              else:
                key2 = 'TUTORIAL'

            elif keys[2] in ('PIPES', 'PLUMBING'):
              idval = 3
              if keys[3] == 'DESCRIPTION':
                key2 = 'DESC'
              else:
                key2 = 'TUTORIAL'

            elif keys[2] in ('CARDS'):
              idval = 4
              if keys[3] == 'DESCRIPTION':
                key2 = 'DESC'
              else:
                key2 = 'TUTORIAL'

            elif keys[2] in ('MATCH3'):
              idval = 5
              if keys[3] == 'DESCRIPTION':
                key2 = 'DESC'
              else:
                key2 = 'TUTORIAL'

            else:
              continue

          elif keys[1] == 'CHRISTMAS' and keys[2] == 'COMICS':
            key1 = keys[2]
            key2 = 'TEXT'
            idval = int(keys[3])

          elif keys[1] == 'TUTORIAL':
            key1 = keys[1]
            key2 = id_
            idval = 0

          elif keys[1] in ('QUEST', 'ITEM', 'SCENE', 'COLLECTION', 'ARTIFACT', 'PUZZLE'):
            key1 = keys[1]
            try:
              key2 = keys[2]
              idval = int(keys[3])
            except (ValueError, IndexError):
              continue

          #IDS_ITEM_(NAME|INFO)_
          #IDS_SCENE_NAME_[0-9]+
          #IDS_QUEST_COLLECTIBLES_(COMPLETED|HINT|QUEST_[12]|TEXT|TITLE)
          else:
            continue

        else:
          continue

        if key1 not in info:
          info[key1] = {}

        if idval not in info[key1]:
          info[key1][idval] = {}

        if key2 not in info[key1][idval]:
          info[key1][idval][key2] = []

        text = text.decode('utf-8')
        if text not in info[key1][idval][key2]:
          info[key1][idval][key2].append(text)

      except:
        sys.stderr.write(line)
        sys.stderr.write('\n')
        raise

  # メンバが１個だけのlistはリストの中身を取り出す
  for k1 in info.keys():
    if not hasattr(info[k1], 'keys'):
      continue

    for k2 in info[k1].keys():
      for k3 in info[k1][k2].keys():
        if isinstance(info[k1][k2][k3], list) and not isinstance(info[k1][k2][k3], basestring):
          if len(info[k1][k2][k3]) == 0:
            info[k1][k2][k3] = None
          elif len(info[k1][k2][k3]) == 1:
            info[k1][k2][k3] = info[k1][k2][k3][0]

  return info


def main():
  if len(sys.argv) < 3:
    sys.stderr.write('Usage: {0} resdir lang [template]\n'.format(sys.argv[0]))
    sys.exit(2)

  textinfo = load_textinfo(sys.argv[1], sys.argv[2])

  if len(sys.argv) > 3 and sys.argv[3] == 'template':
    def make_template(node):
      templ = {}

      for k, v in node.items():
        try:
          n = int(k)
          k = '<id>'
        except ValueError:
          pass

        if isinstance(v, dict):
          if k not in templ:
            templ[k] = {}

          templ[k].update(make_template(v))
        else:
          if k not in templ:
            templ[k] = set()

          templ[k].add(v.__class__.__name__)

      for k, v in templ.items():
        if isinstance(v, set):
          templ[k] = ','.join(v)

      return templ

    print json.dumps(make_template(textinfo), indent=2, sort_keys=True)

  else:
    print json.dumps(textinfo, indent=2, sort_keys=True, ensure_ascii=False).encode('utf-8')

if __name__ == '__main__':
  main()
