#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ts=2 et

import sys
import os
import socket
import json
import signal
import sqlite3
import time
from collections import OrderedDict

DBNAME = 'SelfGift.db'
GIFTER_ID = 'suid_34549937'
GIFTER_NAME = 'SecretSanta'


def split_header(text):
  '''Split HTTP header into keys and values'''
  header = OrderedDict()

  for line in text.split('\r\n'):
    if not header:
      header['request'] = line
    else:
      (key, val) = line.split(':', 1)
      header[key.lower()] = val.strip()

  return header


def forward(request, host, timeout=1.0):
  '''Forward the request to the real destination'''
  if ':' in host:
    (host, port) = host.split(':', 1)
  else:
    port = 80

  addr = socket.gethostbyname(host)

  sock = socket.create_connection((addr, port))
  sock.settimeout(timeout)

  sock.sendall(request)
  reply = []

  try:
    while True:
      data = sock.recv(65536)
      if not data:
        break
      reply.append(data)

  except socket.timeout:
    pass

  sock.close()

  return ''.join(reply)


def fakegifts(giftlist):
  '''Generate a fake gift data'''
  gifts = []

  for (giftid, itemid) in giftlist:
    gift = OrderedDict()
    gift['friend_uid'] = GIFTER_ID
    gift['item'] = OrderedDict()
    gift['item']['colvo'] = 1
    gift['item']['item_id'] = itemid
    gift['item']['item_id_random'] = 68
    gift['item']['picture_id'] = 1
    gift['item']['username'] = GIFTER_NAME
    gift['uid'] = giftid

    gifts.append(gift)

  return gifts


def timestamp():
  return time.strftime('%Y-%m-%d %H:%M:%S')


def process_method(jdata):
  '''Process the SS API method in the request body'''
  print '[{0}] Request: {1}'.format(timestamp(), jdata['methodName'])
 
  fakeres = OrderedDict()

  def adjust_fakeres():
    '''Add fake statistics info to the fake response'''
    fakeres['error'] = False
    fakeres['profiler'] = OrderedDict()
    fakeres['profiler']['name'] = jdata['methodName']
    fakeres['profiler']['mysql'] = 0
    fakeres['profiler']['custom-timers'] = []
    fakeres['version'] = 0
    fakeres['time'] = int(time.time())

  if jdata['methodName'] == 'GetGifts':
    with sqlite3.connect(DBNAME) as conn:
      rows = conn.execute('SELECT giftid, itemid FROM gifts ORDER BY giftid;').fetchall()

    if rows:
      fakeres['response'] = fakegifts(rows)
      adjust_fakeres()
      print json.dumps(fakeres, indent=2)
      return json.dumps(fakeres)

  elif jdata['methodName'] == 'SendGift':
    if jdata['parameters'][1] == GIFTER_ID:
      fakeres['response'] = True
      adjust_fakeres()
      print json.dumps(fakeres, indent=2)
      return json.dumps(fakeres)

  elif jdata['methodName'] == 'SendGiftList':
    if jdata['parameters'][1] == GIFTER_ID:
      fakeres['response'] = [True] * len(jdata['parameters'][2])
      adjust_fakeres()
      print json.dumps(fakeres, indent=2)
      return json.dumps(fakeres)

  elif jdata['methodName'] == 'SendGiftsToAll':
    if jdata['parameters'][1][0][0] == GIFTER_ID:
      fakeres['response'] = [
        [
          GIFTER_ID,
          [True] * len(jdata['parameters'][1][0][1])
        ]
      ]
      adjust_fakeres()
      print json.dumps(fakeres, indent=2)
      return json.dumps(fakeres)

  elif jdata['methodName'] == 'AcceptGiftList':
    with sqlite3.connect(DBNAME) as conn:
      if conn.execute('SELECT giftid FROM gifts LIMIT 1;').fetchone():
        cur = conn.cursor()
        fakeres['response'] = []

        for giftid in jdata['parameters'][1]:
          cur.execute('DELETE FROM gifts WHERE giftid=?;', (giftid,))
          fakeres['response'].append(cur.rowcount > 0)

    if 'response' in fakeres:
      adjust_fakeres()
      print json.dumps(fakeres, indent=2)
      return json.dumps(fakeres)

  elif jdata['methodName'] == 'RestoreOrRegisterApp':
    jdata['parameters'] = [ "6244e627cf2868f1", "6244e627cf2868f1" ]
    return 'Forward modified'

  '''
  elif jdata['methodName'] == 'UpdateInventory':
    items = dict(zip(
      jdata['parameters'][1]['Inventory']['item_id'],
      jdata['parameters'][1]['Inventory']['item_count']
    ))
    for itemid in (2856, 2857, 2858, 2859):
      if itemid in items:
        del items[itemid]

    (jdata['parameters'][1]['Inventory']['item_id'], jdata['parameters'][1]['Inventory']['item_count']) = zip(
      *(sorted(items.items())))
    return 'Forward modified'
    #2856  keyitem   1 "Observation Deck" fragment This is needed to complete the "Observation Deck" photo.  
    #2857  keyitem   1 "Observation Deck" fragment This is needed to complete the "Observation Deck" photo.  
    #2858  keyitem   1 "Observation Deck" fragment This is needed to complete the "Observation Deck" photo.  
    #2859  keyitem   1 "Observation Deck" fragment This is needed to complete the "Observation Deck" photo.  

  elif jdata['methodName'] == 'UpdateProfile':
    if jdata['parameters'][1]['achivement_progress']['a06_puzzles_in_row'] < 4998:
      jdata['parameters'][1]['achivement_progress']['a06_puzzles_in_row'] = 4998
      jdata['parameters'][1]['achivement_progress']['best_puzzles_row'] = 4998
      return 'Forward modified'
  '''


  return None


def do_proxy(conn, jdir):
  conn.settimeout(1)
  request = []

  try:
    while True:
      data = conn.recv(65536)
      if not data:
        break
      request.append(data)

  except socket.timeout:
    pass

  if not request:
    return

  request = ''.join(request)

  try:
    (head, body) = request.split('\r\n\r\n', 1)

    header = split_header(head)
    if header.get('request') != 'POST /hog_ios/jsonway_android.php HTTP/1.0' or \
      header.get('content-type') != 'application/json':
      reply = None

    else:
      jdata = json.loads(body)

      # Write request JSON into local file
      method = jdata['methodName']
      with open(os.path.join(jdir, method + '.req.json'), 'w') as fh:
        fh.write(body)

      reply = process_method(jdata)

      if reply == 'Forward modified':
        reply = None

        body = json.dumps(jdata, indent=2)
        with open(os.path.join(jdir, method + '.req.mod.json'), 'w') as fh:
          fh.write(body)
        
        header['content-length'] = len(body)

        head = []
        for (k, v) in header.items():
          if k == 'request':
            head.append(v)
          else:
            head.append('{0}: {1}'.format(k, v))

        head.append('\r\n')
        head = '\r\n'.join(head)
        with open(os.path.join(jdir, method + '.req.hdr.json'), 'w') as fh:
          fh.write(head)

        request = ''.join([head, body])
        print '[{0}] Forwarding modified request'.format(timestamp())

    if reply:
      reply = '\r\n'.join([
        'HTTP/1.1 200 OK',
        'Server: nginx/1.10.3',
        'Date: {0} GMT'.format(time.strftime('%a, %d %b %Y %H:%M:%S')),
        'Content-Type: application/json',
        'Content-Length: {0}'.format(len(reply)),
        'Connection: close',
        'X-Powered-By: PHP/5.6.30',
        '',
        reply
      ])

    else:
      reply = forward(request, header['host'], 5)
      
      (head, body) = reply.split('\r\n\r\n', 1)
      header = split_header(head)
      try:
        jbody = json.loads(body)

        if jbody['error']:
          result = 'error'
        else:
          result = 'success'

        with open(os.path.join(jdir, method + '.res.json'), 'w') as fh:
          fh.write(body)

      except:
        result = header['request']

      print '[{0}] Forward: {1} {2}'.format(
        timestamp(), method, result)

    sent = 0
    while sent < len(reply):
      sent += conn.send(reply[sent:])

  except StandardError:
    print request
    raise

  finally:
    conn.close()


def initdb():
  with sqlite3.connect(DBNAME) as conn:
    conn.execute('''
CREATE TABLE IF NOT EXISTS gifts (
  giftid INTEGER PRIMARY KEY,
  itemid INTEGER);''')


def main():
  try:
    (port, jdir) = sys.argv[1:]
  except StandardError:
    sys.stderr.write('Usage: {0} listen-port json-dir\n'.format(sys.argv[0]))
    sys.exit(2)

  port = int(port)

  initdb()

  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  sock.bind(('0.0.0.0', port))
  sock.listen(5)

  signal.signal(signal.SIGCHLD, signal.SIG_IGN)

  try:
    print 'Started listening on port {0}...'.format(port)

    while True:
      (conn, _) = sock.accept()

      if os.fork() == 0:
        sock.close()
        do_proxy(conn, jdir)
        os._exit(0)

      else:
        conn.close()

  except KeyboardInterrupt:
    pass


if __name__ == '__main__':
  main()
