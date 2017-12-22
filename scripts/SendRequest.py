#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ts=2 et
import sys
import os
import json
import urllib2
import httplib

PROXIES = {
  'http': {
    "101.53.101.172:9999": 0,
    "111.125.247.158:65103": 0,
    "111.185.153.40:80": 0,
    "113.252.236.56:8080": 0,
    "117.135.198.9:80": 0,
    "118.69.61.57:8888": 0,
    "119.92.172.189:65205": 0,
    "124.133.230.254:80": 0,
    "125.31.19.27:80": 0,
    "128.199.192.236:80": 0,
    "159.89.14.202:3128": 0,
    "159.89.14.214:3128": 0,
    "169.56.111.130:80": 0,
    "177.89.149.121:53281": 0,
    "183.91.3.146:53281": 0,
    "195.123.209.36:80": 0,
    "197.254.29.250:65205": 0,
    "202.159.36.70:80": 0,
    "203.58.117.34:80": 0,
    "203.74.4.0:80": 0,
    "203.74.4.1:80": 0,
    "203.74.4.2:80": 0,
    "203.74.4.4:80": 0,
    "203.74.4.5:80": 0,
    "210.212.73.61:80": 0,
    "211.108.137.74:80": 0,
    "212.83.164.85:80": 0,
    "218.239.138.16:80": 0,
    "218.50.2.102:8080": 0,
    "219.127.253.43:80": 0,
    "223.16.235.56:8080": 0,
    "41.75.76.75:62225": 0,
    "46.235.224.235:80": 0,
    "52.187.34.69:80": 0,
    "66.115.217.163:80": 0,
    "66.70.191.5:3128": 0,
    "83.174.63.181:80": 0,
    "88.119.49.66:63909": 0,
    "91.215.176.27:81": 0,
    "92.38.47.226:80": 0,
    "92.38.47.239:80": 0,
    "94.23.56.95:8080": 0,
    "94.242.222.115:80": 0,
  },
  'https': {
    "118.69.140.108:53281": 0,
    "118.70.12.171:53281": 0,
    "128.199.191.123:443": 0,
    "128.199.74.233:80": 0,
    "128.199.74.233:8080": 0,
    "128.199.74.233:443": 0,
    "128.199.74.233:3128": 0,
    "128.199.75.94:443": 0,
    "139.59.125.77:80": 0,
    "14.142.167.178:3128": 0,
    "165.227.53.107:3128": 0,
    "165.84.167.54:8080": 0,
    "165.98.137.66:53281": 0,
    "175.45.134.96:80": 0,
    "177.67.80.226:3128": 0,
    "177.87.217.199:53281": 0,
    "186.227.8.21:3128": 0,
    "186.46.156.202:65309": 0,
    "186.67.90.13:62225": 0,
    "186.68.85.26:53281": 0,
    "186.83.66.119:63909": 0,
    "187.110.91.154:53281": 0,
    "190.214.31.230:62225": 0,
    "195.154.163.181:3128": 0,
    "200.150.75.162:65103": 0,
    "201.16.197.149:3128": 0,
    "202.138.127.66:80": 0,
    "212.92.250.111:65103": 0,
    "216.100.88.229:8080": 0,
    "41.77.128.18:53005": 0,
    "46.150.174.192:65103": 0,
    "54.36.182.96:3128": 0,
    "82.200.205.49:3128": 0,
    "89.236.17.106:3128": 0,
    "91.191.173.37:808": 0,
    "94.130.14.146:31288": 0,
  }
}

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
    proxies = sorted(PROXIES[proto], key=lambda x: PROXIES[proto][x])
  else:
    proxies = [None]

  for proxy in proxies:
    req = urllib2.Request(
      url='{0}://sh.g5e.com/hog_ios/jsonway_android.php'.format(proto),
      data=body, headers=headers)

    if proxy:
      sys.stderr.write('Using {0}://{1}/\n'.format(proto, proxy))
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

      if proxy:
        PROXIES[proto][proxy] += 1

    except (StandardError, httplib.HTTPException, urllib2.URLError), e:
      sys.stderr.write('{0}: {1}: {2}\n'.format(proxy, e.__class__.__name__, str(e)))
      if proxy:
        PROXIES[proto][proxy] += 1

  else:
    return None

  return json.loads(res)


def load_proxies():
  try:
    with open('proxy-list.json', 'r') as fh:
      jdata = json.load(fh)

    if jdata.get('http') and jdata.get('https'):
      PROXIES['http'] = jdata['http']
      PROXIES['https'] = jdata['https']

  except StandardError:
    pass


def save_proxies():
  with open('proxy-list.json', 'w') as fh:
    json.dump(PROXIES, fh, indent=2, sort_keys=True)


def main():
  if len(sys.argv) < 2:
    sys.stderr.write('Usage: {0} [http|https] {{json|method param}} [...]\n'.format(sys.argv[0]))
    sys.exit(2)

  load_proxies()
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

      try:
        json.dump(json.loads(body), sys.stdout, indent=2)
        sys.stdout.write('\n')
      except StandardError, e:
        sys.stderr.write('{0}: {1}\n'.format(e.__class__.__name__, str(e)))
        sys.stderr.write('{0}\n'.format(body))
        sys.exit(1)

      resp = http_post(body, proto)

      json.dump(resp, sys.stdout, indent=2)
      sys.stdout.write('\n')

  save_proxies()

if __name__ == '__main__':
  main()
