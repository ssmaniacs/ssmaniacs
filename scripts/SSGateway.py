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
MYSELF_ID = 'suid_20699361'
GIFTER_ID = 'suid_34549937'
GIFTER_NAME = 'SecretSanta'


def split_header(text):
  '''Split HTTP header into keys and values'''
  header = OrderedDict()

  for line in text.split('\r\n'):
    if not header:
      header[None] = line
    else:
      (key, val) = line.split(':', 1)
      header[key.lower()] = val.strip()

  return header


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

  if jdata['methodName'] == 'GetGifts':
    with sqlite3.connect(DBNAME) as dbh:
      rows = dbh.execute('SELECT giftid, itemid FROM gifts ORDER BY giftid;').fetchall()

    if rows:
      fakeres['response'] = fakegifts(rows)

  elif jdata['methodName'] == 'SendGift':
    if jdata['parameters'][1] == GIFTER_ID:
      fakeres['response'] = True

  elif jdata['methodName'] == 'SendGiftList':
    if jdata['parameters'][1] == GIFTER_ID:
      fakeres['response'] = [True] * len(jdata['parameters'][2])

  elif jdata['methodName'] == 'SendGiftsToAll':
    if jdata['parameters'][1][0][0] == GIFTER_ID:
      fakeres['response'] = [
        [
          GIFTER_ID,
          [True] * len(jdata['parameters'][1][0][1])
        ]
      ]

  elif jdata['methodName'] == 'AcceptGiftList':
    response = []
    with sqlite3.connect(DBNAME) as dbh:
      if dbh.execute('SELECT giftid FROM gifts LIMIT 1;').fetchone():
        cur = dbh.cursor()

        for giftid in jdata['parameters'][1]:
          cur.execute('DELETE FROM gifts WHERE giftid=?;', (giftid,))
          response.append(cur.rowcount > 0)

    if response:
      fakeres['response'] = response

  elif jdata['methodName'] == 'RestoreOrRegisterApp':
    fakeres['response'] = {
      'new': False,
      'suid': MYSELF_ID,
      'level': 256
    }
    #jdata['parameters'] = [ "6244e627cf2868f1", "6244e627cf2868f1" ]
    #fakeres['forward'] = True

  elif jdata['methodName'] == 'UpdateInventory':
    # modify inventory in the SS server
    items = dict(zip(
      jdata['parameters'][1]['Inventory']['item_id'],
      jdata['parameters'][1]['Inventory']['item_count']
    ))

    # get modification data from database?
    with sqlite3.connect(DBNAME) as dbh:
      cur = dbh.cursor()
      cur.execute('SELECT itemid, count FROM inventory;')

      for (itemid, count) in cur:
        if count:
          items[itemid] = count
          fakeres['forward'] = True
        elif itemid in items:
          del items[itemid]
          fakeres['forward'] = True

    if fakeres['forward']:
      (
        jdata['parameters'][1]['Inventory']['item_id'],
        jdata['parameters'][1]['Inventory']['item_count']
      ) = zip(*(sorted(items.items())))

  '''
  elif jdata['methodName'] == 'UpdateProfile':
    # modify profile data in the SS server
    if jdata['parameters'][1]['achivement_progress']['a06_puzzles_in_row'] < 4998:
      jdata['parameters'][1]['achivement_progress']['a06_puzzles_in_row'] = 4998
      jdata['parameters'][1]['achivement_progress']['best_puzzles_row'] = 4998
      fakeres['forward'] = True
  '''

  if 'response' in fakeres:
    # Add fake statistics info to the fake response
    fakeres['error'] = False
    fakeres['profiler'] = OrderedDict()
    fakeres['profiler']['name'] = jdata['methodName']
    fakeres['profiler']['mysql'] = 0
    fakeres['profiler']['custom-timers'] = []
    fakeres['version'] = 0
    fakeres['time'] = int(time.time())

  return fakeres


def recv_http(sock):
  '''Receive HTTP message (header and body)'''
  message = ''
  headers = None
  msgbody = None

  try:
    sock.settimeout(1.0)

    while True:
      data = sock.recv(4096)
      if not data:
        break

      message += data

      try:
        (head, msgbody) = message.split('\r\n\r\n', 1)
      except StandardError:
        continue

      if not headers:
        headers = split_header(head)

      if int(headers.get('content-length', -1)) == len(msgbody):
        break

  except socket.timeout:
    pass

  return (message, headers, msgbody)


def forward(request, host, timeout=1.0):
  '''Forward the request to the real destination'''
  if ':' in host:
    (host, port) = host.split(':', 1)
    port = int(port)
  else:
    port = 80

  addr = socket.gethostbyname(host)
  sock = socket.create_connection((addr, port))
  sock.settimeout(timeout)

  try:
    sock.sendall(request)
    return recv_http(sock)

  finally:
    sock.close()


def do_proxy(clt, jdir):
  '''intercept SS transmission'''

  # receive request from client
  (request, headers, reqbody) = recv_http(clt)

  if not request:
    return

  try:
    if not headers: # non HTTP message
      reply = None  # forward unchanged

    elif headers.get(None) != 'POST /hog_ios/jsonway_android.php HTTP/1.0' or \
      headers.get('content-type') != 'application/json': # non SS request
      reply = None  # forward unchanged

    else:
      jdata = json.loads(reqbody)

      # Save request JSON into local file
      method = jdata['methodName']
      with open(os.path.join(jdir, method + '.req.json'), 'w') as fh:
        fh.write(reqbody)

      # process SS request
      resp = process_method(jdata)

      if not resp:            # Forward unchanged
        reply = None

      elif 'forward' in resp: # Forward modified
        reply = None

        reqbody = json.dumps(jdata, indent=2)
        with open(os.path.join(jdir, method + '.req.mod.json'), 'w') as fh:
          fh.write(reqbody)
        
        headers['content-length'] = len(reqbody)

        head = []
        for (k, v) in headers.items():
          if k is None:
            head.append(v)
          else:
            head.append('{0}: {1}'.format(k, v))

        head.append('')
        head = '\r\n'.join(head)
        with open(os.path.join(jdir, method + '.req.hdr.json'), 'w') as fh:
          fh.write(head)

        request = '\r\n'.join([head, reqbody])
        print '[{0}] Forwarding modified request'.format(timestamp())

      else:
        print json.dumps(resp, indent=2)
        resbody = json.dumps(resp)

        reply = '\r\n'.join([
          'HTTP/1.1 200 OK',
          'Server: nginx/1.10.3',
          'Date: {0} GMT'.format(time.strftime('%a, %d %b %Y %H:%M:%S')),
          'Content-Type: application/json',
          'Content-Length: {0}'.format(len(resbody)),
          'Connection: close',
          'X-Powered-By: PHP/5.6.30',
          '',
          resbody
        ])

    if not reply:
      # Forward request to the original target
      (reply, reshead, resbody) = forward(request, headers['host'], 5)

      try:
        jbody = json.loads(resbody)

        if jbody['error']:
          result = 'error'
        else:
          result = 'success'

        with open(os.path.join(jdir, method + '.res.json'), 'w') as fh:
          fh.write(resbody)

      except:
        if reshead:
          result = reshead.get(None)
        else:
          result = None

      print '[{0}] Forward: {1} {2}'.format(
        timestamp(), method, result)

    sent = 0
    while sent < len(reply):
      sent += clt.send(reply[sent:])

  except StandardError:
    print request
    raise

  finally:
    clt.close()


def initdb():
  with sqlite3.connect(DBNAME) as dbh:
    dbh.execute('''
CREATE TABLE IF NOT EXISTS gifts (
  giftid INTEGER PRIMARY KEY,
  itemid INTEGER);''')


def main():
  '''Start SS proxying'''
  try:
    (port, jdir) = sys.argv[1:]
  except StandardError:
    sys.stderr.write('Usage: {0} listen-port json-dir\n'.format(sys.argv[0]))
    sys.exit(2)

  port = int(port)

  if not os.path.isdir(jdir):
    os.mkdir(jdir)

  initdb()

  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  sock.bind(('0.0.0.0', port))
  sock.listen(5)

  signal.signal(signal.SIGCHLD, signal.SIG_IGN)

  try:
    print 'Started listening on port {0}...'.format(port)

    while True:
      (clt, _) = sock.accept()

      if os.fork() == 0:
        sock.close()
        do_proxy(clt, jdir)
        os._exit(0)

      else:
        clt.close()

  except KeyboardInterrupt:
    pass


if __name__ == '__main__':
  main()
