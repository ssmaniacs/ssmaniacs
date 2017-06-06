#!/usr/bin/python
# -*- coding: utf-8 -*-
'''ObjectFinderLocal.jsとObjectFinderLocal_<scene>.html, scene_<scene>_*.jsを生成'''

import sys
import os
import re

local_js = '''
function init_local(scene) {{
  local_mode = true;
  document.body.innerHTML = '{0}';
  document.getElementById('scene_sptext').innerHTML = 'ロード中...';
  setTimeout(function(){{ init(scene); }}, 100);
}}

function scene_change_local() {{
  show_spinners();
  var scene = document.getElementById('select_scene').value;
  location.href = 'ObjectFinderLocal_' + scene + '.html';
}}
'''

html_template = '''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Hidden Object Finder</title>
<script src="ObjectFinder.js"></script>
<script src="ObjectFinderLocal.js"></script>
<script src="scene_{scene}_bg.js"></script>
<script src="scene_{scene}_obj.js"></script>
<link rel="stylesheet" type="text/css" href="ObjectFinderLocal.css">
</head>
<body onload="init_local({scene});">
</body>
</html>
'''

def main():
  print 'Generating ObjectFinderLocal.js'
  
  html = []

  with open('../ObjectFinder.html', 'r') as fh:
    body = False
    for line in fh:
      if body:
        line = line.strip()

        line = re.sub(r'<!--.+-->', '', line)
        
        if not line:
          continue

        elif '"lowres"' in line:
          continue

        elif '"scene_change();"' in line:
          line = line.replace('"scene_change();"', '"scene_change_local();"')

        html.append(line.strip())
        if line.startswith('</body>'):
          break

      elif line.startswith('<body '):
        body = True

  with open('ObjectFinderLocal.js', 'w') as fh:
    fh.write(local_js.format(' '.join(html)))


  for scene in range(1, 50):
    print 'Generating ObjectFinderLocal_{0}'.format(scene)
    
    with open('ObjectFinderLocal_{0}.html'.format(scene), 'w') as fh:
      fh.write(html_template.format(scene=scene))

    src = '../scene_{0}_bg.json'.format(scene)
    dst = 'scene_{0}_bg.js'.format(scene)

    if os.path.getmtime(src) > os.path.getmtime(dst):
      with open(src, 'r') as fh:
        jdata = fh.read()
        
      with open(dst, 'w') as fh:
        fh.write('var scene_info =\n')
        fh.write(jdata)
        fh.write(';\n')

    src = '../scene_{0}_obj.json'.format(scene)
    dst = 'scene_{0}_obj.js'.format(scene)

    if os.path.getmtime(src) > os.path.getmtime(dst):
      with open(src, 'r') as fh:
        jdata = fh.read()
        
      with open(dst, 'w') as fh:
        fh.write('var object_info =\n')
        fh.write(jdata)
        fh.write(';\n')

if __name__ == '__main__':
  main()
  