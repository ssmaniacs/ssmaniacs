#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ts=2 et
import sys
import json
import urllib2

def http_post(proto, body, proxy=None):
    headers = {
        'Host': 'sh.g5e.com',
        'X-mytona-fix': '1',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Content-Length': '{0}'.format(len(body)),
        'Accept-Encoding': 'identity, gzip',
    }

    req = urllib2.Request(
        url='{0}://sh.g5e.com/hog_ios/jsonway_android.php'.format(proto),
        data=body, headers=headers)

    if proxy:
        req.set_proxy(proxy, 'http')

    fh = urllib2.urlopen(req, timeout=30.0)

    res = fh.read()

    return json.loads(res)


def main():
  if len(sys.argv) < 2:
    sys.stderr.write('Usage: {0} [http|https] json [...]\n'.format(sys.argv[0]))
    sys.exit(2)

  proto = 'http'
  for arg in sys.argv[1:]:
    if arg in ('http', 'https'):
      proto = arg

    else:
      with open(arg, 'r') as fh:
        body = fh.read()

      sys.stdout.write('Sending {0}\n'.format(arg))
      resp = http_post(proto, body)

      json.dump(resp, sys.stdout, indent=2)
      sys.stdout.write('\n')


if __name__ == '__main__':
  main()
