#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ts=2 et

import sys
import json
import urllib2

# UID with no friend (used to get UID from an Invitation Code)
DUMMY_UID = 'suid_30357589' # (Tate)
#DUMMY_UID = 'suid_48433454' # Zenfone Go

# Use the invide code to know the uid
USE_INVITE = {
    'serviceName': 'GameService',
    'methodName': 'UseInviteCode',
    'parameters': [
        'self-uid', 'invite-code', True, True
    ]
}

USE_INVITE_RESULTS = {
    0: 'SUCCESS',
    2: 'expired code',
    3: 'invalid code',
    4: 'malformed code',
    5: 'already sent',
}

USE_INVITE_RESP_SAMPLE = {
    'response': {
      'result': 0,        # result values 0, 3-5
      'uid': 'peer-uid'   # present only when result = 0
    },
    'error': False,
    'profiler':{ },
    'version':0,
    'time':1504919176
}

DECLINE_INVITE = {
    'serviceName':'GameService',
    'methodName':'DeclineInvite',
    'parameters':[
        'self-uid', 'peer-uid'
    ]
}

DECLINE_INVITE_RESP_SAMPLE = {
  "response": True,
  "error": False,
  "profiler": { },
  "version": 0,
  "time": 1506478428
}

GET_PROFILES = {
    "serviceName": "GameService",
    "methodName": "GetProfiles",
    "parameters": [
        [ 'uid' ],
        None,
        53
    ],
}

GET_INVENTORY = {
    "serviceName": "GameService",
    "methodName": "GetInventory",
    "parameters": [
        "uid"
    ],
}

UPDATE_PROFILE = {
    "serviceName": "GameService",
    "methodName": "UpdateProfile",
    "parameters": [
        "uid",
        {}
    ]
}

UPDATE_INVENTORY = {
    "serviceName": "GameService",
    "methodName": "UpdateInventory",
    "parameters": [
        "uid",
        {}
    ]
}


def http_post(body, proxy=None):
    headers = {
        'Host': 'sh.g5e.com',
        'X-mytona-fix': '1',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Content-Length': '{0}'.format(len(body)),
        'Accept-Encoding': 'identity, gzip',
    }

    req = urllib2.Request(
        url='http://sh.g5e.com/hog_ios/jsonway_android.php',
        data=body, headers=headers)

    if proxy:
        req.set_proxy(proxy, 'http')

    fh = urllib2.urlopen(req, timeout=30.0)

    res = fh.read()

    return json.loads(res)

    resp = http_post(json.dumps(USE_INVITE))
    rslt = resp['response']['result']

    print 'Result: {0} {1}'.format(rslt, USE_INVITE_RESULTS.get(rslt))

    return (rslt == 0)


def uid_from_invite(invite):
  print 'Using InviteCode {0}'.format(invite)
  USE_INVITE['parameters'][0] = DUMMY_UID
  USE_INVITE['parameters'][1] = invite
  resp = http_post(json.dumps(USE_INVITE, indent=2))

  if resp['error'] or resp['response']['result'] != 0:
    sys.stderr.write(json.dumps(resp, indent=2) + '\n')
    sys.exit(1)

  peer_uid = resp['response']['uid']

  DECLINE_INVITE['parameters'][0] = DUMMY_UID
  DECLINE_INVITE['parameters'][1] = peer_uid
  http_post(json.dumps(DECLINE_INVITE, indent=2))

  print 'UID: {0}'.format(peer_uid)
  return peer_uid


PROFESSION = {
  2: 'Merchant',
  4: 'Sage',
  8: 'Sleuth',
  16: 'Magician'
}


def main():
    try:
      (user_old, user_new) = sys.argv[1:]
    except StandardError:
      sys.stderr.write('Usage: {0} old(uid/invite) new(uid/invite)\n'.format(sys.argv[0]))
      sys.exit(2)

    # Get UIDs of both accounts
    if user_old.startswith('suid_'):
      uid_old = user_old
    else:
      uid_old = uid_from_invite(user_old)

    if user_new.startswith('suid_'):
      uid_new = user_new
    else:
      uid_new = uid_from_invite(user_new)

    # Get the latest profile/inventory of both accounts
    GET_PROFILES['parameters'][0][0] = uid_old
    resp = http_post(json.dumps(GET_PROFILES, indent=2))
    profile_old = resp['response'][0]['data']

    GET_PROFILES['parameters'][0][0] = uid_new
    resp = http_post(json.dumps(GET_PROFILES, indent=2))
    profile_new = resp['response'][0]['data']

    GET_INVENTORY['parameters'][0] = uid_old
    resp = http_post(json.dumps(GET_INVENTORY, indent=2))
    inventory_old = resp['response']

    GET_INVENTORY['parameters'][0] = uid_new
    resp = http_post(json.dumps(GET_INVENTORY, indent=2))
    inventory_new = resp['response']

    # Show the current information of both accounts 
    print 'Old user'
    print 'UID\t{0}'.format(profile_old['Profile']['uid'])
    print 'Name\t{0}'.format(profile_old['Profile']['username'])
    print 'Level\t{0}'.format(profile_old['Profile']['level'])
    print 'Prof.\t{0}'.format(PROFESSION[profile_old['Profile']['profession']])
    print 'Device\t{0}, {1}'.format(profile_old['Profile']['idForDevice_ad'],
      profile_old['Profile']['idForDevice_vendor'])
    print
    print 'New user'
    print 'UID\t{0}'.format(profile_new['Profile']['uid'])
    print 'Name\t{0}'.format(profile_new['Profile']['username'])
    print 'Level\t{0}'.format(profile_new['Profile']['level'])
    print 'Prof.\t{0}'.format(PROFESSION[profile_new['Profile']['profession']])
    print 'Device\t{0}, {1}'.format(profile_new['Profile']['idForDevice_ad'],
      profile_new['Profile']['idForDevice_vendor'])
    print

    sys.stdout.write('Clone progress? ')
    sys.stdout.flush()
    ans = sys.stdin.readline().strip().lower()

    if ans != 'y':
      print 'Cancelled'
      sys.exit(1)

    profile_old['Profile']['GameCurrentVersion'] = profile_new['Profile']['GameCurrentVersion']
    profile_old['Profile']['Version'] = profile_new['Profile']['Version']
    profile_old['Profile']['idForDevice_ad'] = profile_new['Profile']['idForDevice_ad']
    profile_old['Profile']['idForDevice_vendor'] = profile_new['Profile']['idForDevice_vendor']
    profile_old['Profile']['uid'] = profile_new['Profile']['uid']
    profile_old['Version'] = profile_new['Version']

    print 'Overwriting profile data'
    UPDATE_PROFILE['parameters'][0] = uid_new
    UPDATE_PROFILE['parameters'][1] = profile_old
    resp = http_post(json.dumps(UPDATE_PROFILE, indent=2))

    print 'Overwriting inventory data'
    UPDATE_INVENTORY['parameters'][0] = uid_new
    UPDATE_INVENTORY['parameters'][1] = inventory_old
    resp = http_post(json.dumps(UPDATE_INVENTORY, indent=2))

    print 'Retrieving the latest data'
    GET_PROFILES['parameters'][0][0] = uid_new
    resp = http_post(json.dumps(GET_PROFILES, indent=2))
    profile_new = resp['response'][0]['data']

    GET_INVENTORY['parameters'][0] = uid_new
    resp = http_post(json.dumps(GET_INVENTORY, indent=2))
    inventory_new = resp['response']

    print 'UID\t{0}'.format(profile_new['Profile']['uid'])
    print 'Name\t{0}'.format(profile_new['Profile']['username'])
    print 'Level\t{0}'.format(profile_new['Profile']['level'])
    print 'Prof.\t{0}'.format(PROFESSION[profile_new['Profile']['profession']])
    print 'Device\t{0}, {1}'.format(profile_new['Profile']['idForDevice_ad'],
      profile_new['Profile']['idForDevice_vendor'])
    print 'Items\t{0} kinds'.format(len(inventory_new['Inventory']['item_id']))


if __name__ == '__main__':
    main()
