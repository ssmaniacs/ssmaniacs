#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ts=2 et
import json
import socket
import sys


def main():
  if len(sys.argv) != 2:
    sys.stderr.write('Usage: {0} req-json\n'.format(sys.argv[0]))
    sys.exit(2)

  with open(sys.argv[1], 'r') as fh:
    body = fh.read()

  json.loads(body)

  req = '\r\n'.join([
    'POST /hog_ios/jsonway_android.php HTTP/1.0',
    'Host: sh.g5e.com',
    'User-Agent: Dalvik/2.1.0 (Linux; U; Android 5.1.1; PLE-701L Build/HuaweiMediaPad)',
    'X-mytona-fix: 1',
    'Content-Type: application/json',
    'Accept: application/json',
    'Content-Length: {0}'.format(len(body)),
    'Accept-Encoding: identity, gzip',
    '',
    body
  ])

  sock = socket.create_connection(('68.168.210.28', 80))
  sock.settimeout(10)

  sock.sendall(req)

  res = []
  try:
    while True:
      data = sock.recv(65536)
      if not data:
        break
      res.append(data)
  except socket.timeout:
    pass

  sock.close()

  if res:
    res = ''.join(res)

    (head, body) = res.split('\r\n\r\n', 1)

    print head.split('\r\n', 1)[0]
    if body:
      print json.dumps(json.loads(body), indent=2)


if __name__ == '__main__':
  main()
