#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ts=2 et

import sys
import os
import json

def main():
  try:
    (lroot, llist, rroot, rlist, sync) = sys.argv[1:]
  except StandardError:
    sys.stderr.write('Usage: {0} local-root local-list remote-root remote-list {{sync|nosync}}\n'.format(sys.argv[0]))
    sys.exit(2)

  lroot = os.path.normpath(os.path.abspath(lroot)) + '/'
  while '//' in lroot:
    lroot = lroot.replace('//', '/')

  if rroot[0] != '/':
    rroot = '/' + rroot

  rroot = os.path.normpath(rroot + '/')
  while '//' in rroot:
    rroot = rroot.replace('//', '/')

  lfiles = {}
  with open(llist, 'r') as fh:
    for line in fh:
      (path, size) = line.strip().split()

      if path.startswith('./'):
        path = path[2:]

      lfiles[path] = int(size)

  #print json.dumps(lfiles, indent=2, sort_keys=True)

  rdirs = ['']
  rfiles = {}
  with open(rlist, 'r') as fh:
    cwd = ''

    for line in fh:
      line = line.strip()

      if line.startswith('./') and line.endswith(':'):
        cwd = line[2:-1]
        rdirs.append(cwd)
        cwd += '/'

      elif line.endswith(':'):
        cwd = line[:-1]
        rdirs.append(cwd)
        cwd += '/'

      elif line.startswith('-rw'):
        fields = line.split()
        rfiles[cwd + fields[8]] = int(fields[4])

  #print json.dumps(rfiles, indent=2, sort_keys=True)
  #sys.stderr.write('\n'.join(rdirs)) 
  #sys.stderr.write('\n')

  diffs = {}
  for key in set(lfiles.keys() + rfiles.keys()):
    lval = lfiles.get(key)
    rval = rfiles.get(key)
    if lval == rval:
      continue

    if '/' in key:
      (path, name) = key.rsplit('/', 1)
    else:
      path = ''
      name = key

    if name[0] == '.':
      continue

    if path not in diffs:
      diffs[path] = []

    if not lval:
      if sync == 'sync':
        diffs[path].append('del {0}'.format(name))
    else:
      diffs[path].append('put {0}'.format(name))

  for (key, val) in sorted(diffs.items()):
    #sys.stderr.write('{0}\n'.format(key))
    if key not in rdirs:
      print 'mkdir {0}'.format(rroot + '/' + key)

    print 'cd {0}'.format(rroot + '/' + key)
    print 'lcd {0}'.format(lroot + '/' + key)
    print '\n'.join(sorted(val))


if __name__ == '__main__':
  main()
