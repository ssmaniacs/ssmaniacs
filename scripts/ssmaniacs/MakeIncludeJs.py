#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ts=2 et
'''SS Maniacs用ヘルパJSを生成する'''

import sys
import os
import re
import time
import json
from xml.etree import ElementTree


def usage():
  sys.stderr.write('Usage: {0} resdir outdir {{progress|itemlist[.en]}} [...]\n'.format(sys.argv[0]))
  sys.exit(2)


def make_progress(resdir, outdir):
  scenes = {}
  root = ElementTree.parse(os.path.join(resdir, '1024',
    'properties', 'data_scenes.xml')).getroot()

  for s in root.findall('scene'):
    scenes[int(s.get('id'))] = [l.find('params').attrib['progress'] for l in s.findall('level')]

  lines = []
  for (k, v) in sorted(scenes.items()):
    lines.append('  {0}: [{1}]'.format(k, ', '.join(v)))

  with open(os.path.join(outdir, 'progress_rate.js'), 'w') as fh:
    fh.write('// SS scene progress rate\n')
    fh.write('// Generated with {0} ({1})\n'.format(
      os.path.basename(__file__), time.strftime('%Y-%m-%d %H:%M:%S')))
    fh.write('var progress_rate = {\n')
    fh.write(',\n'.join(lines))
    fh.write('\n};\n')


def make_itemlist(resdir, outdir, lang):
  srclang = '' if lang == 'en' else '_' + lang
  dstlang = '' if lang == 'ja' else '.' + lang

  srcfile = os.path.join(resdir, '1024', 'properties', 'default' + srclang + '.xml')
  dstfile = os.path.join(outdir, 'itemlist' + dstlang + '.js')

  items = {}
  with open(srcfile, 'r') as fh:
    sys.stderr.write('Reading {0}\n'.format(srcfile))

    for line in fh:
      m = re.match(r'^IDS_ITEM_NAME_(?P<id>[0-9]+):\s*(?P<name>.+)', line)

      if m:
        items[int(m.group('id'))] = m.group('name').strip()

  lines = []
  for (k, v) in sorted(items.items()):
    v = v.replace('&nbsp;', ' ').replace('&', '&amp;').replace('"', '&quot;')
    lines.append('  {0}: "{1}"'.format(k, v))

  with open(dstfile, 'w') as fh:
    fh.write('// SS item name list\n')
    fh.write('// Generated with {0} ({1})\n'.format(
      os.path.basename(__file__), time.strftime('%Y-%m-%d %H:%M:%S')))
    fh.write('var itemlist = {\n')
    fh.write(',\n'.join(lines))
    fh.write('\n};\n')

  
def main():
  if len(sys.argv) < 4:
    usage()

  resdir = sys.argv[1]
  outdir = sys.argv[2]

  for arg in sys.argv[3:]:
    if arg == 'progress':
      make_progress(resdir, outdir)

    elif arg == 'itemlist':
      make_itemlist(resdir, outdir, 'ja')

    elif arg == 'itemlist.en':
      make_itemlist(resdir, outdir, 'en')

    else:
      sys.stderr.write('Ignoring unknown option "{0}"\n'.format(arg))


if __name__ == '__main__':
  main()
