#!/usr/bin/python
# vim: ts=4 et
'''Send gifts anonymously to SS users'''

import sys
import json
import sqlite3
import urllib2
import time
import threading
import Queue
import signal
import httplib
import traceback


import inspect
def trace(msg=''):
#    print '{0}: {1}'.format(inspect.currentframe(1).f_lineno, msg)
    pass


DATABASE = 'AnonymousGift.db'
START_SUID = 'suid_20699361' # ken
START_NAME = 'ken'

GIFTER_SUID = 'suid_00000000'

GIFTER_NAME = 'HappyHalloween'
GIFTER_PIC = 11 # Halloween witch
GIFT_ID = 1797  # Basket of sweets

#GIFTER_NAME = 'SecretSanta'
#GIFTER_PIC = 33 # Christmas girl
#GIFT_ID = 1995  # Gingerbread house

GIFT_COUNT = 10

# Thread control objects
GIFT_TASK = Queue.Queue()
USER_TASK = Queue.Queue()
RESULT_QUEUE = Queue.Queue()
ENDALL = False

# list of known open proxies
PROXIES = [
#    None,
    '101.53.101.172:9999',
    '103.15.251.75:80',
    '104.155.189.170:80',
    '104.155.22.89:80',
    '104.225.155.247:8080',
    '107.170.214.74:80',
    '109.232.107.150:8080',
    '110.170.189.9:80',
    '110.171.228.21:3128',
    '114.215.102.168:8081',
    '114.215.103.121:8081',
    '115.127.68.210:65103',
    '115.85.86.162:65103',
    '117.135.198.11:80',
    '118.151.209.114:80',
    '118.151.209.114:9090',
    '118.70.124.34:65103',
    '120.199.64.163:8081',
    '120.24.208.42:9999',
    '120.25.211.80:9999',
    '120.77.255.133:8088',
    '121.40.199.105:80',
    '122.100.196.34:80',
    '122.192.66.50:808',
    '122.228.253.55:808',
    '123.59.51.130:8080',
    '124.133.230.254:80',
    '124.172.191.51:80',
    '124.246.139.184:8080',
    '125.16.128.118:3128',
    '125.162.156.181:80',
    '128.199.169.17:80',
    '138.197.154.98:80',
    '139.0.26.118:3128',
    '139.162.34.201:8080',
    '139.196.104.28:9000',
    '139.196.170.172:8090',
    '14.141.216.6:3128',
    '142.4.214.9:88',
    '143.0.188.39:80',
    '143.0.189.82:80',
    '149.202.195.236:443',
    '167.114.196.153:80',
    '168.128.29.75:80',
    '168.234.75.142:80',
    '170.82.228.42:8080',
    '171.101.236.116:3128',
    '175.111.131.136:65103',
    '175.194.16.26:80',
    '177.207.234.14:80',
    '177.4.173.242:80',
    '178.27.197.105:80',
    '178.32.213.128:80',
    '180.252.74.147:8080',
    '180.254.181.52:80',
    '180.254.225.18:80',
    '181.221.5.145:80',
    '183.240.87.229:8080',
    '185.141.164.8:8080',
    '185.44.69.44:3128',
    '185.61.190.178:8080',
    '186.103.239.190:80',
    '186.67.90.12:65103',
    '188.0.138.147:8080',
    '188.192.37.202:80',
    '190.152.150.62:65309',
    '190.153.210.237:80',
    '191.253.67.206:8080',
    '192.117.146.110:80',
    '193.108.38.23:80',
    '193.205.4.176:80',
    '193.70.3.144:80',
    '194.44.176.116:8080',
    '195.14.242.39:80',
    '197.254.96.42:53281',
    '200.199.23.220:80',
    '200.229.202.72:3128',
    '200.229.202.72:80',
    '200.229.202.72:8080',
    '200.42.45.211:80',
    '201.21.45.182:80',
    '202.154.182.42:65301',
    '202.159.36.70:80',
    '202.159.36.70:8080',
    '202.162.198.26:65309',
    '202.169.41.186:8080',
    '202.78.227.33:80',
    '202.79.36.119:8080',
    '203.74.4.0:80',
    '203.74.4.1:80',
    '203.74.4.2:80',
    '203.74.4.3:80',
    '203.74.4.4:80',
    '203.74.4.5:80',
    '203.74.4.6:80',
    '203.74.4.7:80',
    '204.11.159.178:53281',
    '208.83.106.105:9999',
    '209.141.61.84:80',
    '209.159.156.199:80',
    '209.198.197.165:80',
    '211.24.107.188:65301',
    '212.1.100.118:53281',
    '212.126.107.182:65103',
    '212.184.12.11:80',
    '212.192.120.42:8080',
    '212.3.173.22:53281',
    '212.83.164.85:80',
    '213.108.201.82:80',
    '213.149.105.12:80',
    '213.168.210.76:80',
    '218.15.25.153:808',
    '218.32.94.77:8080',
    '218.50.2.102:8080',
    '219.91.255.179:80',
    '220.244.27.138:3128',
    '27.131.51.67:443',
    '31.14.40.113:3128',
    '31.42.118.216:53281',
    '31.47.198.61:80',
    '35.154.200.203:80',
    '35.199.36.250:3128',
    '36.66.59.229:65309',
    '36.67.42.123:65103',
    '36.67.78.53:53281',
    '36.85.246.175:80',
    '37.59.36.212:88',
    '40.114.14.173:80',
    '41.242.90.74:65301',
    '41.78.25.185:3128',
    '41.78.25.186:3128',
    '46.38.52.36:8081',
    '47.74.134.234:80',
    '47.90.87.225:88',
    '50.203.117.22:80',
    '51.254.127.194:8080',
    '51.254.127.194:8081',
    '52.41.94.5:80',
    '52.50.247.10:80',
    '52.65.157.207:80',
    '54.158.134.115:80',
    '54.233.168.79:80',
    '58.176.46.248:8380',
    '61.135.155.82:443',
    '61.153.108.142:80',
    '61.153.67.110:9999',
    '61.5.207.102:80',
    '62.210.249.233:80',
    '62.210.51.150:80',
    '62.99.77.124:65103',
    '64.237.61.242:80',
    '64.34.21.84:80',
    '66.70.191.5:3128',
    '72.163.218.146:80',
    '74.118.245.70:80',
    '74.121.141.63:80',
    '78.134.212.173:80',
    '80.1.116.80:80',
    '81.36.128.171:8080',
    '82.165.151.230:80',
    '82.224.48.173:80',
    '82.67.68.28:80',
    '86.102.106.150:8080',
    '88.198.39.58:80',
    '88.209.225.150:53281',
    '88.99.19.93:3128',
    '91.121.88.53:80',
    '91.197.220.51:3128',
    '91.223.12.207:80',
    '92.38.47.226:80',
    '93.170.108.22:3128',
    '93.188.161.129:80',
    '94.153.172.75:80',
    '95.110.189.185:80',
    '95.180.225.7:8080',
    '95.189.123.74:8080',
]


def update_proxy(thread, proxy, close=False, assign=False):
    with sqlite3.connect(DATABASE, timeout=30.0) as dbh:
        cur = dbh.cursor()
        cur.execute('BEGIN IMMEDIATE TRANSACTION;')

        if proxy:
            cur.execute('''
                UPDATE proxy
                SET success = :success, errors = :errors, elapse = :elapse, thread = :thread
                WHERE address = :address;
            ''', {
                'address': proxy['address'],
                'success': proxy['success'],
                'errors': proxy['errors'],
                'elapse': proxy['elapse'],
                'thread': None if close else thread
            })

        if assign:
            row = cur.execute('''
                SELECT address, success, errors FROM proxy
                WHERE thread IS NULL AND (success + errors) < 10
                LIMIT 1;
            ''').fetchone()

            if not row:
                row = cur.execute('''
                    SELECT address, success, errors FROM proxy
                    WHERE thread IS NULL AND (success + errors) >= 10 AND success > errors
                    ORDER BY (CAST(errors AS REAL)/success), errors, elapse, success DESC
                    LIMIT 1;''').fetchone()

            result = {
                'address': row[0],
                'success': row[1],
                'errors': row[2],
            }

            cur.execute('''
                UPDATE proxy
                SET thread = :thread
                WHERE address = :address;''',
                {'address': result['address'], 'thread': thread})
        else:
            result = None

        dbh.commit()

    return result


def handler(signum, frame):
    global ENDALL
    ENDALL = True
    print 'Ctrl+C'


def http_post(body, proxy):
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


def ProxyThread(thread):
    print 'T-{0:02d}: start'.format(thread)

    qbody = {
      "serviceName": "GameService",
      "methodName": "GetFriends",
      "parameters": [
        None,   # suid
        [
#          "Profile.profession",
#          "Profile.level",
          "Profile.username"
        ],
        1000,   # maximum number to get
        0,      # start index
        50      # client program version
      ]
    }

    #XXX dummy request for testing
    '''
    gbody = {
      "serviceName": "GameService",
      "methodName": "SendGift",
      "parameters": [
        GIFTER_SUID,
        None,   # Giftee SUID 
        {
          "colvo": GIFT_COUNT,
          "item_id": GIFT_ID,
          "item_id_random": 68,
          "picture_id": GIFTER_PIC,
          "username": GIFTER_NAME
        },
        None    # timestamp
      ]
    }
    '''
    gbody = {
      "serviceName": "GameService",
      "methodName": "GetClientVersion",
      "parameters": [ None ]
    }

    # Get a unused proxy with least errors
    proxy = update_proxy(thread, None, assign=True)
    print 'T-{0:02d}: now using {1}'.format(thread, proxy['address'])

    recent = []     # result of recent 5 requests
    elapse = []     # elapsed time of recent 10 successful requests
    trial = (proxy['success'] + proxy['errors'] < 10)

    while not ENDALL:
        try:
            #print '{0}: Retrieving task from user queue'.format(proxy)
            (suid, name) = USER_TASK.get(False)
            USER_TASK.task_done()

            try:
                #print '{0}: Querying friends of {1} ({2})'.format(proxy, name, suid)
                qbody['parameters'][0] = suid
                qbody['parameters'][3] = 0  # start index

                friends = []
                while True:
                    # get the list of friends via the assigned proxy
                    start_time = time.time()
                    resp = http_post(json.dumps(qbody), proxy['address'])
                    end_time = time.time()

                    proxy['success'] += 1
                    recent = (recent + [True])[-5:]
                    elapse = (elapse + [end_time - start_time])[-10:]


                    if resp['error']:
                        raise RuntimeError('SS server error')

                    if not resp['response']:
                        break   # no more friends -- next user

                    friends += resp['response']

                    if len(resp['response']) < 1000:
                        break   # no more friends -- next user

                    # get the next 1000 friends
                    qbody['parameters'][3] += 1000

                #print '{0}: Querying friends of {1} ({2}) {3}'.format(proxy, name, suid, len(friends))
                RESULT_QUEUE.put((suid, friends), True)
                #print 'queued'

            except (StandardError, httplib.HTTPException), e:
                print 'T-{0:02d}: {1} {2}'.format(thread, e.__class__.__name__, str(e))
                USER_TASK.put((suid, name), True)

                if not isinstance(e, RuntimeError):
                    proxy['errors'] += 1
                    recent = (recent + [False])[-5:]

        except Queue.Empty:
            #print '{0}: Retrieving task from gift queue'.format(proxy)
            try:
                (suid, name) = GIFT_TASK.get(True, 1.0)
                GIFT_TASK.task_done()
            except Queue.Empty:
                if ENDALL:
                    break
                continue

            if suid is None:
                break

            try:
                #print '{0}: Sending gift to {1} ({2})'.format(proxy, name, suid)
                #XXX gbody['parameters'][1] = suid
                #XXX gbody['parameters'][3] = int(time.time())

                start_time = time.time()
                resp = http_post(json.dumps(gbody), proxy['address'])
                # {"response":18, "error":false, "profiler":{...}, "version":0, "time":...}
                end_time = time.time()

                proxy['success'] += 1
                recent = (recent + [True])[-5:]
                elapse = (elapse + [end_time - start_time])[-10:]

                if resp['error']:
                    raise RuntimeError('SS server error')

                result = (resp.get('response', False) != False)
                #print '{0}: Sending gift to {1} ({2}) {3}'.format(proxy, name, suid, result)
                RESULT_QUEUE.put((suid, result), True)
                #print 'queued'

            except (StandardError, httplib.HTTPException), e:
                print 'T-{0:02d}: {1} {2}'.format(thread, e.__class__.__name__, str(e))
                GIFT_TASK.put((suid, name), True)

                if not isinstance(e, RuntimeError):
                    proxy['errors'] += 1
                    recent = (recent + [False])[-5:]

        if proxy['success'] + proxy['errors'] >= 10:
            if (trial or
                (len(recent) == 5 and len([x for x in recent if not x]) >= 3) or
                (proxy['success'] + proxy['errors'] >= 30 and
                proxy['errors'] > proxy['success'] // 10)):
                # 3 failures in the recent 5 requests
                # or more than 10% failure rate
                proxy['elapse'] = (sum(elapse)/len(elapse)) if elapse else None

                proxy = update_proxy(thread, proxy, close=True, assign=True)
                print 'T-{0:02d}: now using {1}'.format(thread, proxy['address'])
                recent = []
                elapse = []
                trial = (proxy['success'] + proxy['errors'] < 10)
                continue

            if proxy['success'] % 10 == 0:
                proxy['elapse'] = (sum(elapse)/len(elapse)) if elapse else None
                update_proxy(thread, proxy, close=False, assign=False)

        interval = 10
        for i in range(interval):
            if ENDALL:
                break

            time.sleep(1.0)

    proxy['elapse'] = (sum(elapse)/len(elapse)) if elapse else None
    update_proxy(thread, proxy, close=True, assign=False)
    print '{0}: done'.format(thread)


def add_gifts(dbh, gifts, limit):
    cur = dbh.cursor()
    cur.execute('BEGIN IMMEDIATE TRANSACTION;')

    # Select ungifted users with the latest activity in the last 7 days
    sql = '''
        SELECT suid, name
        FROM users
        WHERE gifted is NULL
        AND updated > strftime('%s', 'now', '-7 day')
        ORDER BY distance, updated DESC
        {0};'''.format('LIMIT {0}'.format(limit) if limit > 0 else '')

    cur.execute(sql)

    added = 0
    for (suid, name) in cur.fetchall():
        try:
            if suid not in gifts:
                GIFT_TASK.put((suid, name), False)
                cur.execute('''
                    UPDATE users SET gifted = 0 WHERE suid = :suid;
                ''', {'suid': suid})
                gifts[suid] = name
                added += 1

        except Queue.Full:
            print 'Gift task queue full'
            break

    dbh.commit()

    print 'Added {0} gift tasks'.format(added)

    return added


def add_users(dbh, users, limit):
    cur = dbh.cursor()
    cur.execute('BEGIN IMMEDIATE TRANSACTION;')

    # Select unfollowed users with the latest activity in the last 7 days
    sql = '''
        SELECT suid, name, distance
        FROM users
        WHERE followed IS NULL
        AND updated > strftime('%s', 'now', '-7 day')
        ORDER BY distance, updated DESC
        {0};'''.format('LIMIT {0}'.format(limit) if limit > 0 else '')

    cur.execute(sql)

    added = 0
    for (suid, name, distance) in cur.fetchall():
        try:
            if suid not in users:
                USER_TASK.put((suid, name), False)
                cur.execute('''
                    UPDATE users SET followed = 0 WHERE suid = :suid;
                ''', {'suid': suid})
                users[suid] = (name, distance)
                added += 1

        except Queue.Full:
            print 'User task queue full'
            break

    dbh.commit()

    print 'Added {0} follow tasks'.format(added)

    return added


def process_users(dbh):
    # start task threads
    qthreads = []
    while len(qthreads) < 30:
        th = threading.Thread(target=ProxyThread, args=(len(qthreads)+1,))
        th.start()
        qthreads.append(th)

    more_users = True
    gifts = {}
    users = {}

    global ENDALL
    while True:
        trace()
        if (not ENDALL) and more_users:
            # Get ungifted users from database
            if len(gifts) < 100:
                new_gifts = add_gifts(dbh, gifts, 100)

                # When not enough ungifted users in database
                if new_gifts < 100 and len(users) < 5:
                    # Add follow user tasks
                    add_users(dbh, users, 5)
                    if not users:   # no more un-followed users
                        more_users = False

        trace()
        if not gifts and not users:
            #print 'Exitting main thread'
            break

        trace()
        try:
            (suid, result) = RESULT_QUEUE.get(True, 60)
            RESULT_QUEUE.task_done()
        except Queue.Empty:
            trace()
            break

        if isinstance(result, list):
            trace()
            added = 0
            updated = 0

            # update database
            cur = dbh.cursor()
            cur.execute('BEGIN IMMEDIATE TRANSACTION;')

            trace()
            for friend in result:
                trace(friend['uid'])
                try:
                    trace()
                    cur.execute('''
                        INSERT INTO users (suid, name, distance, updated)
                        VALUES(:suid, :name, :distance, :updated);
                    ''', {
                        'suid': friend['uid'],
                        'name': friend['data']['Profile']['username'],
                        'distance': users[suid][1] + 1,
                        'updated': int(friend['last_update']),
                    })
                    trace()

                    added += cur.rowcount

                except sqlite3.IntegrityError:
                    trace()
                    cur.execute('''
                        UPDATE users
                        SET updated = :updated
                        WHERE suid = :suid AND updated < :updated;
                    ''', {
                        'suid': friend['uid'],
                        'updated': int(friend['last_update']),
                    })
                    trace()

                    updated += cur.rowcount

            trace()
            cur.execute('''
                UPDATE users
                SET followed = strftime('%s', 'now')
                WHERE suid = :suid;
            ''', {'suid': suid})

            trace()
            dbh.commit()

            print '\t\t{0} ({1}) has {2} friends, {3} new, {4} updated'.format(
                users[suid][0], suid, len(result), added, updated)

            del users[suid]

        else:
            trace()
            if result == True:
                cur = dbh.cursor()
                cur.execute('BEGIN IMMEDIATE TRANSACTION;')
                cur.execute('''
                    UPDATE users SET gifted = 1 WHERE suid = :suid;
                ''', {'suid': suid})
                dbh.commit()

                print '\t\t{0} ({1}) has received the gift'.format(
                    gifts[suid], suid)

            del gifts[suid]


    # stop worker threads
    print 'Stopping all threads'
    ENDALL = True

    for t in qthreads:
        GIFT_TASK.put(None)

    for t in qthreads:
        t.join()


def database_init(dbh):
    # user management table
    dbh.execute('''CREATE TABLE IF NOT EXISTS users (
        suid TEXT PRIMARY KEY NOT NULL,
        name TEXT,
        updated INTEGER,
        distance INTEGER,
        followed INTEGER,
        gifted INTEGER);''')

    dbh.execute('''CREATE INDEX IF NOT EXISTS users_1 ON users(updated);''')

    # reset start user's last update time and followed flag
    try:
        dbh.execute('''
            INSERT INTO users (suid, name, distance, updated)
            VALUES (:suid, :name, 0, strftime('%s', 'now'));
        ''', {'suid': START_SUID, 'name': START_NAME})
    except sqlite3.IntegrityError:
        dbh.execute('''
            UPDATE users
            SET updated = strftime('%s', 'now'), followed = NULL
            WHERE suid = :suid;
        ''', {'suid': START_SUID})

    # reset followed flag of users who were followed more than 7 days ago
    # and updated after that time
    # and whose following did not complete (followed == 0)
    dbh.execute('''
        UPDATE users
        SET followed = NULL
        WHERE followed < strftime('%s', 'now', '-7 days')
        AND followed < updated;
    ''')

    # reset gifted flag of users whose gifting did not complete
    dbh.execute('''UPDATE users SET gifted = NULL WHERE gifted = 0;''')

    # proxy management table
    dbh.execute('''CREATE TABLE IF NOT EXISTS proxy (
        address TEXT PRIMARY KEY NOT NULL,
        success INTEGER DEFAULT 0,
        errors INTEGER DEFAULT 0,
        elapse REAL,
        thread INTEGER);''')

    for proxy in PROXIES:
        dbh.execute('''
            INSERT OR IGNORE INTO proxy (address) VALUES(:address);
        ''', {'address': proxy})

    dbh.execute('''UPDATE proxy SET thread = NULL WHERE thread IS NOT NULL;''')

    dbh.commit()


def main():
    signal.signal(signal.SIGINT, handler)
    try:
        with sqlite3.connect(DATABASE, timeout=30.0) as dbh:
            database_init(dbh)
            process_users(dbh)

    except:
        traceback.print_exc()
        raise

    finally:
        ENDALL = True
        sys.exit(0)


if __name__ == '__main__':
    main()
