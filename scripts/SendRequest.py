#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ts=2 et
import sys
import os
import json
import urllib2

PROXIES = [
  "66.70.191.5:3128",
  "47.90.87.225:88",
  "165.227.144.174:80",
#  "24.38.71.43:80",
  "203.58.117.34:80",
  "120.199.64.163:8081",
  "183.240.87.229:8080",
  "143.0.189.82:80",
  "202.159.36.70:80",
  "120.77.255.133:8088",
  "120.24.208.42:9999",
  "203.146.82.253:80",
  None
]

SELF_UID = 'suid_20699361'

def http_post(body, proto='http', use_proxy=True):
  '''可能であればプロキシ経由でSSリクエストを送る'''
  headers = {
    'Host': 'sh.g5e.com',
    'X-mytona-fix': '1',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Content-Length': '{0}'.format(len(body)),
    'Accept-Encoding': 'identity, gzip',
  }

  if use_proxy:
    proxies = PROXIES
  else:
    proxies = [None]

  for proxy in proxies:
    req = urllib2.Request(
    url='{0}://sh.g5e.com/hog_ios/jsonway_android.php'.format(proto),
    data=body, headers=headers)

    if proxy:
      req.set_proxy(proxy, proto)

    try:
      fh = urllib2.urlopen(req, timeout=30.0)
      res = fh.read()
      break

    except urllib2.HTTPError, e:
      sys.stderr.write('{0}: {1}: {2}\n'.format(proxy, e.__class__.__name__, str(e)))
      if e.code == 400:
        res = e.read()
        break

    except (StandardError, urllib2.URLError), e:
      sys.stderr.write('{0}: {1}: {2}\n'.format(proxy, e.__class__.__name__, str(e)))

  else:
    return None

  return json.loads(res)


def main():
  if len(sys.argv) < 2:
    sys.stderr.write('Usage: {0} [http|https] {{json|method param}} [...]\n'.format(sys.argv[0]))
    sys.exit(2)

  proto = 'http'
  method = None

  for arg in sys.argv[1:]:
    if arg in ('http', 'https'):
      proto = arg

    elif method is None:
      if os.path.exists(arg):
        with open(arg, 'r') as fh:
          body = fh.read()

        sys.stdout.write('Sending {0}\n'.format(arg))
        resp = http_post(body, proto)

        json.dump(resp, sys.stdout, indent=2)
        sys.stdout.write('\n')

      else:
        method = arg

    else:
      body = '''{{
  "serviceName": "GameService",
  "methodName": "{method}",
  "parameters": [{params}]
}}'''.format(method=method, params=arg.replace('self', '"' + SELF_UID + '"'))

      json.dump(json.loads(body), sys.stdout, indent=2)
      sys.stdout.write('\n')

      resp = http_post(body, proto)

      json.dump(resp, sys.stdout, indent=2)
      sys.stdout.write('\n')


if __name__ == '__main__':
  main()
