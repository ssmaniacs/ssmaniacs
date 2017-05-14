#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ts=2 et
import sys
import os
import json
from xml.etree import ElementTree


HTML_HEAD = '''<!DOCTYPE html>
<html>
  <head>
    <title>{title}</title>
    <meta charset='utf-8'>
    <meta name='viewport' content='width=device-width,initial-scale=1'>
  </head>
  <body>
'''
HTML_TAIL = '''
</body>
</html>
'''


def load_textfile(basedir, lang):
  '''表示用テキスト情報を読み込む'''
  if lang == 'en':
    filename = 'default.xml'
  else:
    filename = 'default_{0}.xml'.format(lang)

  textinfo = {}
  with open(os.path.join(basedir, '1024', 'properties', filename), 'r') as fh:
    for line in fh:
      if ':' in line:
        (key, val) = line.split(':', 1)
        textinfo[key] = val.strip()

  return textinfo


def load_collections(basedir):
  '''コレクション情報を読み込む'''
  with open(os.path.join(basedir, '1024', 'properties', 'collections.json'), 'r') as fh:
    jdata = json.load(fh)

  collections = [[]]
  artifacts = []
  
  for c in jdata:
    if c['type'] == 'collection':
      if len(collections[-1]) >= 100:
        collections.append([])
        
      collections[-1].append(c)
    elif c['type'] == 'artifact':
      artifacts.append(c)
    else:
      print c
      raise RuntimeError('unknown type')

  return (collections, artifacts)


def load_iteminfo(basedir):
  '''アイテム情報（ギフト可否）を読み込む'''
  root = ElementTree.parse(os.path.join(basedir, '1024', 'properties', 'items.xml')).getroot()
  
  items = {}
  for item in root:
    id_ = int(item.get('id'))
    try:
      nogift = int(item.get('nogift'))
    except StandardError:
      nogift = 0
      
    items[id_] = nogift

  return items


def write_index(collections, artifacts, textinfo, dstdir):
  '''索引ページを出力する'''
  with open(os.path.join(dstdir, 'collections.html'), 'w') as fh:
    title = 'Secret Society {0}'.format(textinfo['IDS_COLLECTIONS'])
    fh.write(HTML_HEAD.format(title=title))
    
    fh.write('''
<a href='index.html'>[HOME]</a><hr>
<h1>{title}</h1>
<ul>
'''.format(title=title))

    htmllist = []
    
    info = {
        'html': 'collections_all.html',
        'title': '全{0} &amp; {1} (画像なし)'.format(textinfo['IDS_COLLECTIONS'], textinfo['IDS_ARTIFACTS']),
        'list': collections + [artifacts],
        'sections': []
    }
    
    fh.write('<li><a href="{html}">{title}</a></li>'.format(
      html=info['html'], title=info['title']))

    htmllist.append(info)
    
    idx = 1
    caption = textinfo['IDS_COLLECTIONS']
    for c in collections:
      info = {
        'html': 'collections_{0}.html'.format(idx),
        'list': [c]
      }
      idx += 1
      
      if htmllist:
        info['prev'] = htmllist[-1]['html']
        htmllist[-1]['next'] = info['html']

      min_ = c[0]['id']
      max_ = c[-1]['id']
      info['title'] = '{cap} {min}-{max}'.format(cap=caption, min=min_, max=max_)
      htmllist[0]['sections'].append((info['html'], info['title']))

      fh.write('<li><a href="{html}">{title}</a></li>'.format(
        html=info['html'], title=info['title']))

      htmllist.append(info)

    info = {
      'html': 'artifacts.html',
      'title': textinfo['IDS_ARTIFACTS'],
      'list': [artifacts],
    }

    if htmllist:
      htmllist[0]['sections'].append((info['html'], info['title']))
      info['prev'] = htmllist[-1]['html']
      htmllist[-1]['next'] = info['html']
    
    htmllist.append(info)
    fh.write('<li><a href="{html}">{cap}</a></li>'.format(
        html=info['html'], cap=info['title']))

    fh.write('</ul>\n')
    fh.write(HTML_TAIL.format(title=title))
  
  return htmllist


def write_collist(colinfo, textinfo, iteminfo, dstdir):
  '''コレクションリストを出力する'''
  listall = (len(colinfo['list']) > 1)

  with open(os.path.join(dstdir, colinfo['html']), 'w') as fh:
    title = 'Secret Society {0}'.format(colinfo['title'])
    fh.write(HTML_HEAD.format(title=title))

    # ナビゲーションバーを出力
    navi = [
      "<a href='index.html'>[HOME]</a>",
      "<a href='collections.html'>[UP]</a>",
    ]
    
    if 'prev' in colinfo:
      navi.append("<a href='{0}'>[PREV]</a>".format(colinfo['prev']))
    else:
      navi.append("<font color=gray>[PREV]</font>")
      
    if 'next' in colinfo:
      navi.append("<a href='{0}'>[NEXT]</a>".format(colinfo['next']))
    else:
      navi.append("<font color=gray>[NEXT]</font>")

    fh.write('&nbsp;'.join(navi))

    # メインタイトルを出力
    fh.write('<hr>\n<h1>{0}</h1>\n'.format(colinfo['title']))
  
    # ALLリストの場合、セクションインデックスを出力
    if 'sections' in colinfo:
      fh.write('<ul>\n')

      for (h, t) in colinfo['sections']:
        fh.write('<li><a href="#{0}">{1}</a></li>\n'.format(h.split('.', 1)[0], t))

      fh.write('</ul>\n<hr>\n')

    # リストテーブルを出力
    secidx = 0
    
    for collist in colinfo['list']:
      if listall:
        (h, t) = colinfo['sections'][secidx]
        secidx += 1
        fh.write('<h2><a name="{0}">{1}</a></h2>\n'.format(h.split('.', 1)[0], t))

      if collist[0]['type'] == 'artifact':
        typename = textinfo['IDS_ARTIFACTS']
      else:
        typename = textinfo['IDS_COLLECTIONS']

      fh.write('''
    <table border='1' bgcolor='#FFDD88' cellpadding='5'>
    <tr>
    <th>No.</th>
    <th>{0}名</th>
    <th>アイテム1</th>
    <th>アイテム2</th>
    <th>アイテム3</th>
    <th>アイテム4</th>
    <th>アイテム5</th>
    <th>{0}</th>
    <th>エレメント</th>
    <th>報酬</th>
    <th>ギフト</th>
    </tr>
'''.format(typename))

      for c in collist:
        line = [
          '<tr>'
          '<td align="right">{0}</td>'.format(c['id']),
        ]

        if c['type'] == 'collection':
          name = textinfo['IDS_COLLECTION_NAME_{0}'.format(c['id'])]
        elif c['type'] == 'artifact':
          name = textinfo['IDS_ARTIFACT_NAME_{0}'.format(c['id'])]
        
        line.append('<td>{0}</td>'.format(name))
        
        nogift = 0
        
        for i in c['items'] + [c['main_item_id']]:
          name = textinfo['IDS_ITEM_NAME_{0}'.format(i)]

          if listall:
            line.append('<td>{name}</td>'.format(name=name))
          else:
            img = 'images/items/{0}.png'.format(i)
            line.append('<td align="center" valign="top" width="120"><img src="{img}"><br>{name}</td>'.format(name=name, img=img))

          nogift += iteminfo.get(i, 0)

        elem = []
        for e in c['charges']:
          elem.append('{0} x{1}'.format(textinfo['IDS_ITEM_NAME_{0}'.format(e['id'])], e['count']))

        line.append('<td>{0}</td>'.format('<br>'.join(elem)))

        rew = []
        for r in c['rewards']:
          rew.append('{0} x{1}'.format(textinfo['IDS_ITEM_NAME_{0}'.format(r['id'])], r['count']))

        line.append('<td>{0}</td>'.format('<br>'.join(rew)))
        
        if nogift > 1 or c['type'] == 'artifact':
          line.append('<td bgcolor=#dd4444>NG</td>')
        else:
          line.append('<td>OK</td>')
        
        line.append('</tr>')
        line.append('')

        fh.write('\n'.join(line))

      fh.write('</table>\n')
      
      if listall:
        fh.write('<div align="right"><a href="#">[TOP]</a></div>\n')

    fh.write('<hr>\n')
    fh.write('&nbsp;'.join(navi))
    fh.write(HTML_TAIL)


def main():
  try:
    (basedir, dstdir, lang) = sys.argv[1:]
  except StandardError:
    sys.stderr.write('Usage: {0} basedir dstdir lang\n'.format(sys.argv[0]))
    sys.exit(2)

  textinfo = load_textfile(basedir, lang)
  (collections, artifacts) = load_collections(basedir)
  iteminfo = load_iteminfo(basedir)

  htmllist = write_index(collections, artifacts, textinfo, dstdir)

  for html in htmllist:
    write_collist(html, textinfo, iteminfo, dstdir)


if __name__ == '__main__':
  main()
