#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ts=2 et
import sys
import json
import httplib
import urllib2
import time
import traceback

from ItemList import ITEMS

SELF_UID = "suid_20699361"
SELF_NAME = "ken"
SELF_PIC = 1

ACCEPT_USERS = [
    "suid_34549937", "suid_00000000"
]

PROXIES = {
  "66.70.191.5:3128": 0,
  "47.90.87.225:88": 0,
  "165.227.144.174:80": 0,
  "24.38.71.43:80": 0,
  "203.58.117.34:80": 0,
  "120.199.64.163:8081": 0,
  "183.240.87.229:8080": 0,
  "143.0.189.82:80": 0,
  "202.159.36.70:80": 0,
  "120.77.255.133:8088": 0,
  "120.24.208.42:9999": 0,
  "203.146.82.253:80": 0,
}

def http_post(body, proto='http'):
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

    for proxy in sorted(PROXIES, key=lambda x: x[1]):
      req.set_proxy(proxy, 'http')

      try:
        fh = urllib2.urlopen(req, timeout=30.0)
        res = fh.read()
        break

      except urllib2.HTTPError, e:
        sys.stderr.write('{0}: {1}: {2}\n'.format(proxy, e.__class__.__name__, str(e)))
        if e.code == 400:
          res = e.read()
          break

      except (StandardError, urllib2.URLError, httplib.HTTPException), e:
        sys.stderr.write('{0}: {1}: {2}\n'.format(proxy, e.__class__.__name__, str(e)))
        PROXIES[proxy] += 1

    return json.loads(res)


def accept_gifts():

  print 'Peeking the gift box'
  body = {
    "serviceName": "GameService",
    "methodName": "GetGifts",
    "parameters": [ SELF_UID ]
  }
  resp = http_post(json.dumps(body))
  '''
  {
    "response": [
        {
            "friend_uid": "suid_20560225", 
            "item": {
                "colvo": 1, 
                "item_id": 318, 
                "picture_id": 6, 
                "username": "heike"
            }, 
            "uid": 0
        }, 
    ], 
  }
  '''
  print '{0} gifts in the gift box'.format(len(resp['response']))

  accepts = []
  thanks = {}
  for gift in resp['response']:
    itemid = gift['item']['item_id']
    itemname = ITEMS.get(itemid, 'item:{0}'.format(itemid))

    if itemid == 318: 
      #action = 'accept'
      action = 'ignore'

    elif gift['friend_uid'] not in ACCEPT_USERS:
      action = 'thank'

    else:
      action = 'ignore'

    if action != 'accept':
      print '{0}\t{1} from {2}'.format(
        action, itemname, gift['item']['username'])

    if action == 'accept':
      accepts.append(gift['uid'])

    elif action == 'thank':
      accepts.append(gift['uid'])
      if gift['friend_uid'] not in thanks:
        thanks[gift['friend_uid']] = 1
      else:
        thanks[gift['friend_uid']] += 1

  print '{0} gifts to accept'.format(len(accepts))
  if not accepts:
    return

  body = {
    "serviceName": "GameService",
    "methodName": "AcceptGiftList",
    "parameters":[ SELF_UID, accepts ]
  }

  resp = http_post(json.dumps(body))
  #print json.dumps(body, indent=2)
  #resp = {}
  try:
    if resp['error']:
      print 'AcceptGiftList error'
    else:
      print '{0} gifts accepted'.format(len([x for x in resp['response'] if x]))
  except StandardError:
    traceback.print_exc()

  print '{0} users to thank'.format(len(thanks))
  if not thanks:
    return

  body = {
    "serviceName": "GameService",
    "methodName": "SendGiftsToAll",
    "parameters": [
      SELF_UID,
      [
      #[
      #   "suid_10251407",
      #   [
      #      {
      #         "colvo" : 1,
      #         "item_id" : 318,
      #         "picture_id" : 1,
      #         "username" : "ken"
      #      }
      #   ]
      #],
      ]
    ]
  }

  gift = {
    "colvo": 1,
    "item_id": 318,
    "picture_id": SELF_PIC,
    "username": SELF_NAME
  }

  for (peer, count) in thanks.items():
    body['parameters'][1].append([peer, [gift] * count])

  #print json.dumps(body, indent=2)

  resp = http_post(json.dumps(body))

  #print json.dumps(resp, indent=2)

  friends = 0
  gifts = 0
  for res in resp['response']:
    friends += 1
    gifts += len([x for x in res[1] if x])

  print 'Sent {0} thank-yous to {1} friends'.format(gifts, friends)


def main():
  if len(sys.argv) > 1:
    try:
      interval = int(sys.argv[1])
    except:
      sys.stderr.write('Usage: {0} [interval]\n'.format(sys.argv[0]))
      sys.exit(2)

  else:
    interval = -1

  while True:
    accept_gifts()
    print time.strftime('%Y-%m-%d %H:%M:%S')

    if interval > 0:
      print 'Sleeping {0} seconds'.format(interval)
      time.sleep(interval)

    else:
      break

  sys.exit(0)


if __name__ == '__main__':
  main()

