#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ts=2 et
import sys
import os
import re
import json
from xml.etree import ElementTree


ITEMTYPE = {
  'talisman': 0,
  'amulet':   1,
  'energy':   2,
  'power':    3,
  'keyitem':  4,
  'element':  5,
  'banish':   6,
  'collitem': 7,
  'collection': 8,
  'oneshot':  9,
  'tool':     10,
  'chest':    11,
  'artifact': 98,
  'special':  99,
}

def load_itemdata(resdir, langs):
  '''read item info from the game resource file'''
  items = {}

  # items.xml: アイテム種別情報
  with open(os.path.join(resdir, '1024', 'properties', 'items.xml'), 'r') as fh:
    root = ElementTree.parse(fh).getroot()

  for i in root:
    id_ = None
    type_ = None

    for (k, v) in i.items():
      k = k.lower()
      if k == 'id':
        id_ = int(v)
      elif k == 'sectype':
        type_ = int(v)

    items[id_] = {'TYPE': type_ }

  # items.xmlに記載されていないアイテムがある？
  with open(os.path.join(resdir, '1024', 'properties', 'collections.json'), 'r') as fh:
    jdata = json.load(fh)

  for i in jdata:
    type_ = ITEMTYPE[i['type']]

    if i['main_item_id'] not in items:
      items[i['main_item_id']] = {'TYPE': type_}

    if i['type'] == 'collection':
      type_ = ITEMTYPE['collitem']
    else:
      type_ = ITEMTYPE['collection']

    for sub in i['items']:
      if sub not in items:
        items[sub] = {'TYPE': type_}

      items[sub]['COMBINE'] = i['main_item_id']

  # 言語ごとのテキストを読み込む
  for lang in langs:
    if lang in (None, '', 'en'):
      path = os.path.join(resdir, '1024', 'properties', 'default.xml')
    else:
      path = os.path.join(resdir, '1024', 'properties', 'default_{0}.xml'.format(lang))

    with open(path, 'r') as fh:
      for line in fh:
        if not (line.startswith('IDS_ITEM_INFO_') or line.startswith('IDS_ITEM_NAME_')):
          continue

        line = line.strip()

        key, val = line.split(':', 1)
        keys = key.split('_')

        try:
          infotype = keys[2]
          itemid = int(keys[3])
          if len(keys) > 4:
            subid = int(keys[4])
          else:
            subid = 0

        except:
          continue

        val = val.replace('&nbsp;', ' ').replace('&cr;', ' ')

        if itemid not in items:
          items[itemid] = {}

        if lang not in items[itemid]:
          items[itemid][lang] = {}

        if infotype not in items[itemid][lang]:
          items[itemid][lang][infotype] = [val]
        else:
          if subid > 0:
            items[itemid][lang][infotype][-1] += '<>' + val
          elif val not in items[itemid][lang][infotype]:
            items[itemid][lang][infotype].append(val)

  return items


SPECIAL = [
  318, 847, 1000, 1001, 1002, 1003, 1004, 1005, 1010, 1011, 1012, 1013, 1020,
  1021, 1022, 1663, 1669, 1943, 1986, 2117, 2222, 2395, 2533, 2651, 2892, 2995,
  3072, 3311, 3419, 3636, 3640, 3852, 3856, 4304, 4308, 4535, 4540]


def main():
  if len(sys.argv) < 3:
    sys.stderr.write('Usage: {0} resdir jsondir [lang|inventory|type|itemid [...]]\n'.format(sys.argv[0]))
    sys.stderr.write('type: ' + ' '.join(sorted(ITEMTYPE.keys())) + '\n')
    sys.exit(2)

  resdir = sys.argv[1]
  jsondir = sys.argv[2]

  langs = []
  items = []
  types = []
  ownedonly = False

  for a in sys.argv[3:]:
    if re.match('^[a-z]{2}$', a):
      langs.append(a)

    elif a == 'inventory':
      # 持っているアイテムのみ
      ownedonly = True

    elif a in ITEMTYPE:
      # タイプに該当するアイテムのみ
      types.append(ITEMTYPE[a])

      if a == 'special':
        items += SPECIAL

    else:
      # 指定IDのアイテムのみ
      try:
        items.append(int(a))
      except ValueError:
        sys.stderr.write('Invalid itemid {0}\n'.format(a))
        sys.exit(2)

  iteminfo = load_itemdata(resdir, langs)

  with open(os.path.join(jsondir, 'UpdateInventory.req.json'), 'r') as fh:
    jdata = json.load(fh)

    inventory = dict(zip(
      jdata['parameters'][1]['Inventory']['item_id'],
      jdata['parameters'][1]['Inventory']['item_count']))

  # print result
  line = ['id', 'type', 'combine', 'inventory']

  for l in langs:
    line.append('name({0})'.format(l))
    line.append('info({0})'.format(l))

  line.append('remark')

  print '\t'.join(line)

  typename = dict([(v, k) for (k, v) in ITEMTYPE.items()])

  for itemid, item in sorted(iteminfo.items()):
    if ownedonly and itemid not in inventory:
      continue

    if types and item.get('TYPE') not in types and itemid not in items:
      # 明示TYPEに含まれていなければ, 明示ITEMに含まれなければならない
      continue

    if items and itemid not in items and item.get('TYPE') not in types:
      # 明示ITEMに含まれていなければ, 明示TYPEに含まれなければならない
      continue

    combine = item.get('COMBINE')
    line = [
      str(itemid),
      typename.get(item.get('TYPE'), 'unknown'),
      str(combine) if combine else '',
      str(inventory.get(itemid, 0)),
    ]
    remark = ''

    if line[1] == 'oneshot' and itemid in SPECIAL:
      if ITEMTYPE['special'] in types:
        line[1] = 'special'
      else:
        continue

    for l in langs:
      if l in item:
        name = item[l]['NAME']
        info = item[l].get('INFO', [])
        if len(name) > 1 or len(info) > 1:
          remark = 'conflict'

        line.append('\\n'.join(name))
        line.append('\\n'.join(info))
      else:
        line.append('')
        line.append('')

    line.append(remark)

    print '\t'.join(line)


if __name__ == '__main__':
  main()
