# /usr/bin/python
# -*- coding: utf-8 -*-
# vim: ts=2 et
'''Automatically send gifts on wishlists'''
import sys
import os
import socket
import json
import time

#GIFTER_ID = 'suid_34549937'
#GIFTER_NAME = 'SecretSanta'
GIFTER_ID = 'suid_20699361'
GIFTER_NAME = 'ken'

ELEMENTS = [
  259, 260, 261, 262, 263, 264, 265, 266, 267, 543, 544, 545, 546,
  547, 548, 549, 550, 551, 552, 553, 554, 555, 556, 557, 558, 559,
  560, 561, 562, 563, 564, 565, 566, 567, 568, 569, 1799, 1800, 1801,
  1802, 1803, 1804, 1935, 1936, 1937, 1938, 1939, 1940, 1941, 1942,
  1982, 1983, 1984, 1985, 2124, 2125, 2126, 2127, ] 

CHARGES = {
  'firefl': 847,
  'carrot': 1663,
  'arrow': 2117,
  'bug': 2222,
  'token': 2892,
}

def load_itemname(resdir):
  items = {}
  with open(os.path.join(resdir, '1024/properties/default.xml'), 'r') as fh:
    for line in fh:
      if line.startswith('IDS_ITEM_NAME_'):
        try:
          (key, name) = line.strip().split(':', 1)
          items[int(key.rsplit('_', 1)[-1])] = name
        except StandardError:
          pass

  return items


def sendreq(body):
  '''Send and recerive http message'''
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
    (head, body) = ''.join(res).split('\r\n\r\n', 1)
    return (head.split('\r\n', 1)[0], json.loads(body))
  else:
    return (None, None)


def sendgifts(uid, name, items):
  print 'Sending {0} items to {1}'.format(len(items), name)

  for (item, name) in items:
    reqbody = {
      "serviceName": "GameService",
      "methodName": "SendGift",
      "parameters": [
        GIFTER_ID,
        uid,
        {
          "colvo" : 1,
          "item_id" : item,
          "item_id_random" : 68,
          "picture_id" : 1,
          "username" : GIFTER_NAME
        },
        int(time.time())
      ]
    }

    (status, resbody) = sendreq(json.dumps(reqbody))
    #status = 'SUPPRESSED'
    #resbody = {'error': True}

    try:
      if resbody['error']:
        res = 'error'
      elif resbody['response']:
        res = 'success'
      else:
        res = 'fail'

      print '{item:4d} {name}\tHTTP:{stat} result:{res}'.format(
        name=name, item=item, stat=status, res=res)
    except:
      pass

    time.sleep(1)

  print


def main():
  try:
    resdir = sys.argv[1]
  except StandardError:
    resdir = '.'

  itemname = load_itemname(resdir)

  reqbody = {
    "serviceName": "GameService",
    "methodName": "GetFriends",
    "parameters": [
      GIFTER_ID,
      [
        "Profile.profession",
        "Profile.level",
        "Profile.experience",
        "Profile.username",
        "Wishes"
      ],
      5000,
      0,
      46
    ]
  }

  (status, friends) = sendreq(json.dumps(reqbody))

  if friends['error']:
    print json.dumps(friends, indent=2)
    return

  idx = 0
  for f in friends['response']:
    idx += 1
    try:
      if f['data']['Wishes']:
        wishes = f['data']['Wishes']['item_id']
      else:
        wishes = []

      # profession
      # 2 = Merchant 商人
      # 4 = Sage 賢者
      # 8 = Sleuth 密偵
      # 16 = Magician 魔術師
      job = f['data']['Profile']['profession']
      if job == 2:
        jobname = 'Merchant'
      elif job == 4:
        jobname = 'Sage'
      elif job == 8:
        jobname = 'Sleuth'
      elif job == 16:
        jobname = 'Magician'
      else:
        jobname = 'Unknown job ({0})'.format(job)

      #print 'uid:    {0}'.format(f['uid'])
      #print 'name:   {0}'.format(f['data']['Profile']['username'])
      #print 'job:    {0}'.format(jobname)
      #print 'exp:    {0}'.format(f['data']['Profile']['experience'])
      #print 'level:  {0}'.format(f['data']['Profile']['level'])
      #print 'wishes: {0}'.format(wishes)

      uid = f['uid']
      if len(uid) > 13:
        uid = uid[:10] + '...'

      uname = f['data']['Profile']['username']

      print '{idx}/{total} {name:<16} ({uid:<13})'.format(
        idx=idx, total=len(friends['response']), name=uname, uid=uid
      )

      for (k, v) in CHARGES.items():
        if k in uname.lower():
          wishes.append(v)

      if wishes:
        gifts = {}
        for item in wishes:
          name = itemname.get(item, '')
          if item in ELEMENTS:
            gifts['E'] = (item, name)
          elif item in CHARGES.values():
            gifts['S'] = (item, name)
          else:
            gifts['C'] = (item, name)

          print '{0:4d} {1}'.format(item, name)

        sendgifts(f['uid'], uname, gifts.values())
      else:
        print 'None\n'

    except StandardError:
      print f
      raise

if __name__ == '__main__':
  main()
