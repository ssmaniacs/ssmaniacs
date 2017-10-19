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


NONAME = {
  350:  "firewater",                # Огненная вода
  351:  "cornucopia",               # Рог изобилия
  352:  "ambrosia",                 # Пища богов
  353:  "manna",                    # Манна небесная
  354:  "water of life",            # Живая вода
  593:  "venetia",                  # venetia
  594:  "venetia",                  # venetia
  595:  "venetia",                  # venetia
  611:  "throne room",              # тронный зал
  612:  "throne room",              # тронный зал
  858:  "philosopher's stone",      # филосовский кристалл
  1000: "experience",               # Опыт
  1001: "energy",                   # Энергия
  1003: "reputation",               # Репутация
  1005: "power",                    # Сила
  2020: "number of gifts",          # кол-во подарков
  2364: "fifth element",            # пятый элемент
  3635: "magic box",                # Волшебная шкатулка
  3863: "letter in expanded form",  # Письмо в развернутом виде
  3864: "chest of fireflies",       # Сундучок со Светлячками
  3865: "chest of ladybugs",        # Сундучок с Божьими коровками
  3866: "chest of carrots",         # Сундучок с Морковками
  3867: "chest of arrows",          # Сундучок со Стрелами Амура
  3868: "chest of tokens",          # Сундучок с Жетонами
}

def load_itemdata(resdir, langs):
  '''read item info from the game resource file'''
  items = {}

  # items.xml: アイテム種別情報
  with open(os.path.join(resdir, '1024', 'properties', 'items.xml'), 'r') as fh:
    #root = ElementTree.parse(fh).getroot()
    root = ElementTree.fromstring(fh.read().replace('/ >', ' />'))


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
        m = re.match(r'IDS_ITEM_(?P<type>INFO|NAME)_(?P<id>[0-9]+):\s*(?P<text>.+)', line)

        if not m:
          continue

        infotype = m.group('type')
        itemid = int(m.group('id'))
        text = m.group('text').strip()

        text = text.replace('&nbsp;', ' ').replace('&cr;', ' ')

        if itemid not in items:
          items[itemid] = {}

        if lang not in items[itemid]:
          items[itemid][lang] = {}

        if infotype not in items[itemid][lang]:
          items[itemid][lang][infotype] = [text]
        else:
          items[itemid][lang][infotype].append(text)

  return items


SPECIAL = [
  318, 847, 1000, 1001, 1002, 1003, 1004, 1005, 1010, 1011, 1012, 1013, 1020,
  1021, 1022, 1663, 1669, 1943, 1986, 2117, 2222, 2395, 2533, 2651, 2892, 2995,
  3072, 3311, 3419, 3636, 3640, 3852, 3856, 4304, 4308, 4535, 4540]


def main():
  if len(sys.argv) < 2:
    sys.stderr.write('Usage: {0} resdir [lang|type|itemid [...]]\n'.format(sys.argv[0]))
    sys.stderr.write('type: ' + ' '.join(sorted(ITEMTYPE.keys())) + '\n')
    sys.exit(2)

  resdir = sys.argv[1]

  langs = []
  items = []
  types = []

  for a in sys.argv[2:]:
    if re.match('^[a-z]{2}$', a):
      langs.append(a)

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

  '''
  with open(os.path.join(jsondir, 'UpdateInventory.req.json'), 'r') as fh:
    jdata = json.load(fh)

    inventory = dict(zip(
      jdata['parameters'][1]['Inventory']['item_id'],
      jdata['parameters'][1]['Inventory']['item_count']))

    #sys.stderr.write(json.dumps(inventory, indent=2, sort_keys=True))
  '''
  inventory = {}

  # print result
  line = ['id', 'type', 'combine', 'inventory']

  for l in langs:
    line.append('name({0})'.format(l))
    line.append('info({0})'.format(l))

  line.append('remark')

  print '\t'.join(line)

  typename = dict([(v, k) for (k, v) in ITEMTYPE.items()])

  for itemid, iteminfo in sorted(iteminfo.items()):

    if types and iteminfo.get('TYPE') not in types and itemid not in items:
      # 明示TYPEに含まれていなければ, 明示ITEMに含まれなければならない
      continue

    if items and itemid not in items and iteminfo.get('TYPE') not in types:
      # 明示ITEMに含まれていなければ, 明示TYPEに含まれなければならない
      continue


    combine = iteminfo.get('COMBINE')
    line = [
      str(itemid),
      typename.get(iteminfo.get('TYPE'), 'unknown'),
      str(combine) if combine else '',
      str(inventory.get(itemid, 0)),
    ]
    remark = ''

    '''
    if line[1] == 'oneshot' and itemid in SPECIAL:
      if ITEMTYPE['special'] in types or not types:
        line[1] = 'special'
      else:
        sys.stderr.write('SKIP: {0}\t{1}\n'.format(itemid, iteminfo.get('en', {}).get('NAME')))
        continue
    '''

    for l in langs:
      if l in iteminfo:
        name = iteminfo[l]['NAME']
        info = iteminfo[l].get('INFO', [])
        if len(name) > 1 or len(info) > 1:
          remark = 'conflict'

        line.append('\\n'.join(name))
        line.append('\\n'.join(info))
      else:
        line.append('NONAME:' + NONAME.get(int(line[0]), ''))
        line.append('')

    line.append(remark)

    print '\t'.join(line)


if __name__ == '__main__':
  main()
