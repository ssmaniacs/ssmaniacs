#!/usr/bin/python

import sys
import urllib2
import json
import time
import sqlite3

GET_WAITINGS = {
    "methodName": "GetWaitings",
    "parameters": [
        "suid_20699361",
        [ "Profile.username" ],
        53
    ],
    "serviceName": "GameService"
}

GET_WAITINGS_RESP_SAMPLs = {
  "error": False,
  "response": {
    "fb_waiting_them": [],
    "waiting_them": [
      {
        "version": None,
        "data": {
          "Profile": {
            "username": "Agne"
          }
        },
        "uid": "suid_47981316",
        "last_update": 1505036942
      }
    ],
    "fb_waiting_us": [],
    "waiting_us": []
  },
  "profiler": {},
  "version": 0,
  "time": 1505041306
}
 
GET_INVITE = {
    'serviceName':'GameService',
    'methodName':'GenerateInviteCode',
    'parameters':[ 'userid' ]
}

GET_INVITE_RESP_SAMPLE = {
    'response':'invite-code',
    'error':False,
    'profiler':{},
    'version':0,
    'time':1497451802
}          

USE_INVITE = {
    'serviceName':'GameService',
    'methodName':'UseInviteCode',
    'parameters':[
        'suid_20699361', 'invite-code', True, True
    ]
}

USE_INVITE_RESP_SAMPLE = {
    'response':{'result':3,'uid':None},
    'error':False,
    'profiler':{},
    'version':0,
    'time':1504919176
}

USE_INVITE_RESULTS = {
    0: 'SUCCESS',
    3: 'invalid code',
    4: 'malformed code',
    5: 'already sent',
}

DECLINE_INVITE = {
    "serviceName": "GameService",
    "methodName": "DeclineInvite",
    "parameters": [
        "suid_20699361", "invitee-suid"
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

def add_friend(suid):
    print 'Asking invite code for {0}'.format(suid)
    GET_INVITE['parameters'][0] = suid
    resp = http_post(json.dumps(GET_INVITE))
    code = resp['response']

    print 'Using invite code {0}'.format(code)
    USE_INVITE['parameters'][1] = code
    resp = http_post(json.dumps(USE_INVITE))
    rslt = resp['response']['result']

    print 'Result: {0} {1}'.format(rslt, USE_INVITE_RESULTS.get(rslt))

    return (rslt == 0)

def decline_invite(suid):
    print 'Declining {0}'.format(suid)
    DECLINE_INVITE['parameters'][1] = suid
    resp = http_post(json.dumps(DECLINE_INVITE))

    print 'Result: {0} {1}'.format(rslt, resp['response'])

    return resp['response']


def main():
    try:
        count = int(sys.argv[1])
    except:
        count = -1

    # Load already invited suid's
    done = {}
    with open('AddFriends.done', 'r') as fh:
        for line in fh:
            (uid, ts) = line.strip().split('\t')
            done[uid.strip()] = int(ts.strip())
 
    # Get current waiting list
    resp = http_post(json.dumps(GET_WAITINGS))
    waiting = len(resp['response']['waiting_them'])
    print 'Currently {0} friends in waiting'.format(waiting)

    # Purge stale invitations (more than 7 days old)
    for user in resp['response']['waiting_them']:
        suid = user['uid']

        if suid in done and done[suid] < time.time() - (60 * 60 * 24 * 7):
            decline_invite(suid)
            waiting -= 1

    count = 99 - waiting
    if count == 0:
        sys.exit(0)

    print 'Inviting {0} friends'.format(count)

    with sqlite3.connect('AnonymousGift.db') as dbh:
        cur = dbh.cursor()
        cur.execute('SELECT suid FROM users WHERE distance > 1 ORDER BY updated DESC;')

        for (suid,) in cur:
            if suid in done:
                continue

            try:
                if add_friend(suid):
                    done[suid] = int(time.time())
                    count -= 1
                    if count == 0:
                        break
            except Exception, e:
                print '{0} {1}'.format(e.__class__.__name__, str(e)) 
    
            time.sleep(5)

    with open('AddFriends.done', 'w') as fh:
        for (suid, ts) in done.items():
            fh.write('{0}\t{1}\n'.format(suid, ts))


if __name__ == '__main__':
    main()
