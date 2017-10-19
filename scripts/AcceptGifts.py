#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ts=2 et
import sys
import json
import urllib2
import time
import traceback

from ItemList import *

SELF_UID = "suid_20699361"
SELF_NAME = "ken"

PROXIES = {
  "66.70.191.5:3128",
  "47.90.87.225:88",
  "165.227.144.174:80",
  "24.38.71.43:80",
  "203.58.117.34:80",
  "120.199.64.163:8081",
  "183.240.87.229:8080",
  "143.0.189.82:80",
  "202.159.36.70:80",
  "120.77.255.133:8088",
  "120.24.208.42:9999",
  "203.146.82.253:80",
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

    for proxy in PROXIES:
      req.set_proxy(proxy, 'http')

      try:
        fh = urllib2.urlopen(req, timeout=30.0)
        res = fh.read()
        break
      except (StandardError, urllib2.URLError), e:
        sys.stderr.write('{0}: {1}\n'.format(e.__class__.__name__, str(e)))

    return json.loads(res)


def main():

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
  thanks = []
  for gift in resp['response']:
    itemid = gift['item']['item_id']

    if itemid == 318: 
      itemname = 'Thank-you'
      action = 'accept'

    elif itemid in COLLECT:    
      itemname = COLLECT[itemid]
      action = 'thank'

    elif itemid in COLLNEW:
      itemname = COLLNEW[itemid]
      action = 'ignore'

    elif itemid in ELEMENT:
      itemname = ELEMENT[itemid]
      action = 'thank'

    elif itemid in SPECIAL:
      itemname = SPECIAL[itemid]
      action = 'thank'

    else:
      itemname = 'item:{0}'.format(itemid)
      action = 'ignore'

    if action != 'accept':
      print '{0}\t{1} from {2}'.format(action, itemname, gift['item']['username'])

    if action == 'accept':
      accepts.append(gift['uid'])

    elif action == 'thank':
      accepts.append(gift['uid'])
      thanks.append(gift['friend_uid'])

  print '{0} thank-you gifts'.format(len(accepts) - len(thanks))
  print '{0} gifts to accept'.format(len(accepts) - (len(accepts) - len(thanks)))
  if not accepts:
    sys.exit(0)

  try:
    if sys.argv[1] == 'peek':
      sys.exit(0)
  except IndexError:
    pass

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

  print '{0} gifts to thank'.format(len(thanks))
  if not thanks:
    sys.exit(0)

  for peer in thanks:
    body = {
      "serviceName": "GameService",
      "methodName": "SendGift",
      "parameters": [
        SELF_UID,
        peer,
        {
          "colvo" : 1,
          "item_id" : 318,
          "item_id_random" : 68,
          "picture_id" : 1,
          "username" : SELF_NAME
        },
        int(time.time())
      ]
    }
    resp = http_post(json.dumps(body))
    #print json.dumps(body, indent=2)
    #resp = {}
    print 'Sent thank-you to {0}'.format(peer)


if __name__ == '__main__':
  main()

