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


def load_sceneinfo(xmlpath, resdir):
  '''シーンの画像定義を読み込む'''
  root = ElementTree.parse(xmlpath).getroot()
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


def convert_image(scene, resdir, imgdir):
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


def load_scenelist(resdir):
  '''シーンID、XMLファイルパス一覧を読み込む'''
  root = ElementTree.parse(os.path.join(resdir, '1024',
    'properties', 'data_scenes.xml')).getroot()
 
  xmllist = {}

  for scene in root.findall('scene'):
    xmllist[int(scene.get('id'))] = os.path.join(resdir, '1024', scene.get('xml'))

  return xmllist


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


def encode_img(path):
  with open(path, 'rb') as fh:
    return 'data:image/png;base64,' + base64.b64encode(fh.read())


def output_json(id, sceneinfo, imgdir, textinfo, template, mode):
  '''シーンイメージ情報をJSONに出力'''
  if mode == 'path':
    bgfile = 'scene_{0}_bgp.json'.format(id)
    objfile = 'scene_{0}_objp.json'.format(id)
    embed = False
  else:
    bgfile = 'scene_{0}_bg.json'.format(id)
    objfile = 'scene_{0}_obj.json'.format(id)
    embed = True

  scene = sceneinfo['name']

  sys.stderr.write('Generating image info for {0}\n'.format(scene))

  # バックグラウンドイメージ情報をレイヤ順に格納
  bginfo = []

  for (layer, images) in sorted(sceneinfo['background'].items()):
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

  with open(bgfile, 'w') as fh:
    json.dump(bginfo, fh, indent=2, sort_keys=True)

  # オブジェクトイメージ情報を格納
  objinfo = {
    'form': [],
    'part': [],
    'morph': []
  }

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

  for form in sceneinfo['objects']['form']:
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


  for part in sceneinfo['objects']['part']:
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

  for morph in sceneinfo['objects']['morph']:
    obj = {}
    obj['name'] = morph['name']
    obj['images'] = []

    for item in morph['images']:
      obj1 = {}
      for (tag, img) in item.items():
        obj1[tag] = copy_imgitem(img, 'morph')

      obj['images'].append(obj1)

    objinfo['morph'].append(obj)

  with open(objfile, 'w') as fh:
    fh.write(json.dumps(objinfo, indent=2, sort_keys=True, ensure_ascii=False).encode('utf-8'))


def main():
  if len(sys.argv) < 5:
    sys.stderr.write('Usage: {0} resdir imgdir lang {{dump|conv|json-path|json-data}} [xml ...]\n'.format(sys.argv[0]))
    sys.stderr.write('''
1. conv コマンドで変換リストを生成する
   $ ./{0} ... conv > convlist.tsv

2. convert_images.sh で変換を実施
   $ ./convert_imagges.sh convlist.tsv

3. json-path コマンドでjson (イメージパス版) を出力する
   (scene_ID_bgp.json, scene_ID_objp.json)

4. ObjectFinder.htmlをパス版jsonで実行 (ObjectFinder.html?image_root=path&bg_control=true)

5. scene_template.jsonを適宜修正 ("type":"skip", "type":"effect" の追記など)

6. json-data コマンドでjson (イメージ埋め込み版) を出力する （または EmbedImageData.py)
   (scene_ID_bg.json, scene_ID_obj.json)
'''.format(sys.argv[0]))

    sys.exit(2)

  (resdir, imgdir, lang, output) = sys.argv[1:5]

  if len(sys.argv) == 5:
    # シーンXML一覧を読み込む
    xmllist = load_scenelist(resdir)
  else:
    # 指定されたシーン定義XMLをターゲットとする
    xmllist = {}
    for arg in sys.argv[5:]:
      id = int(arg.rsplit('.', 1)[0].rsplit('_', 1)[-1])
      xmllist[id] = arg

  if output[:4] == 'json':
    textinfo = load_textinfo(resdir, lang);
    with open('scene_template.json', 'r') as fh:
      template = json.load(fh)

  # 各シーンのイメージ情報を読み込む
  for (id, xml) in sorted(xmllist.items()):
    sys.stderr.write('Processing: {0}\n'.format(xml))
    sceneinfo = load_sceneinfo(xml, resdir)

    if output == 'dump':
      print json.dumps(sceneinfo, indent=2)

    elif output == 'conv':
      # メイン画像・マスク画像合成用のリストを生成
      #   メイン.jpg<TAB>マスク.jpg<TAB>ターゲット.png
      #   メイン.png<TAB>-<TAB>ターゲット.png
      # ImageMagick convert で合成：
      #   convert メイン マスク \( -clone 0 -alpha extract \) ￥
      #     \( -clone 1 -clone 2 -compose multiply -composite \) \
      #     -delete 1,2 -alpha off -compose copy_opacity -composite ターゲット
      convert_image(sceneinfo, resdir, imgdir)

    elif output in ('json-path', 'json-data'):
      output_json(id, sceneinfo, imgdir, textinfo, template.get(str(id), {}), output[-4:])

if __name__ == '__main__':
  main()
