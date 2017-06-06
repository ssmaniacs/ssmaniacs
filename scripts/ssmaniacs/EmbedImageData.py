#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import json
import base64

def main():
  if len(sys.argv) < 2:
    sys.stderr.write('Usage: {0} imgdir\n')
    sys.exit(2)
  
  imgdir = sys.argv[1]
  
  sys.stderr.write('Reading JSON from stdin\n')
  jdata = json.load(sys.stdin)
  
  def walk(node):
    if isinstance(node, list) and not isinstance(node, basestring):
     for i in node:
        walk(i)
        
    elif isinstance(node, dict):
      if 'path' in node:
        try:
          with open(os.path.join(imgdir, node['path']), 'rb') as fh:
            node['data'] = 'data:image/png;base64,' + base64.b64encode(fh.read())
        except:
          raise
          pass
  
      for i in node.values():
        walk(i)

    else:
     pass
     
  walk(jdata)
  
  print json.dumps(jdata, indent=2, ensure_ascii=False).encode('utf-8')
  
if __name__ == '__main__':
  main()