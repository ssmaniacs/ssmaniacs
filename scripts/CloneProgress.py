#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ts=2 et

import sys
import json
import urllib2

DUMMY_UID = 'suid_303575'  # id without a friend

# Use the invide code to know the uid
USE_INVITE = {
    'serviceName':'GameService',
    'methodName':'UseInviteCode',
    'parameters':[
        DUMMY_UID, 'invite-code', True, True
    ]
}

USE_INVITE_RESULTS = {
    0: 'SUCCESS',
    3: 'invalid code',
    4: 'malformed code',
    5: 'already sent',
}

USE_INVITE_RESP_SAMPLE = {
    'response':{
      'result':0,   # result values 0, 3-5
      'uid':'uid_'  # uid (only when result = 0)
    },
    'error':False,
    'profiler':{},
    'version':0,
    'time':1504919176
}

DECLINE_INVITE = {
    'serviceName':'GameService',
    'methodName':'UseInviteCode',
    'parameters':[
        DUMMY_UID, None,
    ]
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
        "suid_",
        {}
    ]
}

UPDATE_INVENTORY = {
    "serviceName": "GameService",
    "methodName": "UpdateInventory",
    "parameters": [
        "suid_",
        {}
    ]
}


def http_post(body, proxy=None):
    headers = {
        'Host': 'sh.g5e.com',
        #'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 5.1.1; PLE-701L Build/HuaweiMediaPad)',
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

profession = {
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

    if user_old.startswith('suid_'):
      uid_old = user_old
    else:
      USE_INVITE['parameters'][1] = user_old
      resp = http_post(json.dumps(USE_INVITE, indent=2))

      if resp['error'] or resp['response']['result'] != 0:
        sys.stderr.write(json.dumps(resp, indent=2) + '\n')
        sys.exit(1)

      uid_old = resp['response']['uid']

      DECLINE_INVITE['parameters'][1] = uid_old
      http_post(json.dumps(DECLINE_INVITE, indent=2))


    if user_new.startswith('suid_'):
      uid_new = user_new
    else:
      USE_INVITE['parameters'][1] = user_new
      resp = http_post(json.dumps(USE_INVITE, indent=2))

      if resp['error'] or resp['response']['result'] != 0:
        sys.stderr.write(json.dumps(resp, indent=2) + '\n')
        sys.exit(1)

      uid_new = resp['response']['uid']

      DECLINE_INVITE['parameters'][1] = uid_new
      http_post(json.dumps(DECLINE_INVITE, indent=2))


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

    print 'Old user'
    print 'UID: {0}'.format(profile_old['Profile']['uid'])
    print 'Name: {0}'.format(profile_old['Profile']['username'])
    print 'Level: {0}'.format(profile_old['Profile']['level'])
    print 'Profession: {0}'.format(profession[profile_old['Profile']['profession']])
    print 'Device ID: {0}, {1}'.format(profile_old['Profile']['idForDevice_ad'], profile_old['Profile']['idForDevice_vendor'])
    print 'Achievements: {0}'.format(len(inventory_old.get('GameCenterAchievments', 0))-1)
    print
    print 'New user'
    print 'UID: {0}'.format(profile_new['Profile']['uid'])
    print 'Name: {0}'.format(profile_new['Profile']['username'])
    print 'Level: {0}'.format(profile_new['Profile']['level'])
    print 'Profession: {0}'.format(profession[profile_new['Profile']['profession']])
    print 'Device ID: {0}, {1}'.format(profile_new['Profile']['idForDevice_ad'], profile_new['Profile']['idForDevice_vendor'])
    print 'Achievements: {0}'.format(len(inventory_new.get('GameCenterAchievments', 0))-1)
    print

    sys.stdout.write('Clone progress? ')
    sys.stdout.flush()
    ans = sys.stdin.readline().strip().lower()

    if ans != 'y':
      sys.exit(1)

    profile_old['Profile']['GameCurrentVersion'] = profile_new['Profile']['GameCurrentVersion']
    profile_old['Profile']['Version'] = profile_new['Profile']['Version']
    profile_old['Profile']['idForDevice_ad'] = profile_new['Profile']['idForDevice_ad']
    profile_old['Profile']['idForDevice_vendor'] = profile_new['Profile']['idForDevice_vendor']
    profile_old['Profile']['uid'] = profile_new['Profile']['uid']
    profile_old['Version'] = profile_new['Version']

    UPDATE_PROFILE['parameters'][0] = uid_new
    UPDATE_PROFILE['parameters'][1] = profile_old
    resp = http_post(json.dumps(UPDATE_PROFILE, indent=2))

    UPDATE_INVENTORY['parameters'][0] = uid_new
    UPDATE_INVENTORY['parameters'][1] = inventory_old
    resp = http_post(json.dumps(UPDATE_INVENTORY, indent=2))


if __name__ == '__main__':
    main()
