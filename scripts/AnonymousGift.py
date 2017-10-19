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
import collections

from logging import getLogger, StreamHandler, DEBUG, INFO
loglevel = DEBUG #INFO
logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(loglevel)
logger.setLevel(loglevel)
logger.addHandler(handler)
logger.propagate = False


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
REQUEST_QUEUE = Queue.PriorityQueue()
RESULT_QUEUE = Queue.Queue()
ENDALL = False

# list of known open proxies
PROXY_LOCK = threading.Lock()
PROXY_LIST = collections.OrderedDict()
PROXIES = [
    '101.53.101.172:9999',
    '103.15.251.75:80',
    '104.155.189.170:80',
    '104.155.22.89:80',
    '104.225.155.247:8080',
    '107.170.214.74:80',
    '109.232.107.150:8080',
    '109.88.40.240:80',
    '110.170.189.9:80',
    '110.171.228.21:3128',
    '114.112.252.245:80',
    '114.215.102.168:8081',
    '114.215.103.121:8081',
    '115.124.70.137:52305',
    '115.127.68.210:65103',
    '115.85.86.162:65103',
    '117.135.198.11:80',
    '117.135.198.9:80',
    '117.2.128.168:8888',
    '118.151.209.114:80',
    '118.151.209.114:9090',
    '118.69.61.57:8888',
    '118.70.124.34:65103',
    '118.97.129.219:8080',
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
    '128.199.192.236:80',
    '138.197.114.250:80',
    '138.197.154.98:80',
    '139.0.26.118:3128',
    '139.162.34.201:8080',
    '139.162.69.213:8081',
    '139.196.104.28:9000',
    '139.196.170.172:8090',
    '14.141.216.6:3128',
    '14.203.99.67:8080',
    '142.4.214.9:88',
    '143.0.188.26:80',
    '143.0.188.39:80',
    '143.0.189.82:80',
    '149.202.195.236:443',
    '163.121.188.2:8080',
    '163.121.188.3:8080',
    '163.172.59.200:8080',
    '165.227.144.174:80',
    '167.114.196.153:80',
    '168.128.29.75:80',
    '168.234.75.142:80',
    '170.82.228.42:8080',
    '171.101.236.116:3128',
    '173.212.243.187:80',
    '175.111.131.136:65103',
    '175.194.16.26:80',
    '176.31.174.1:9999',
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
    '186.178.10.78:65103',
    '186.46.156.202:65309',
    '186.46.90.50:53281',
    '186.67.90.12:65103',
    '186.68.85.26:53281',
    '188.0.138.147:8080',
    '188.192.37.202:80',
    '189.206.107.6:8080',
    '190.11.26.58:52305',
    '190.117.115.150:65103',
    '190.152.150.62:65309',
    '190.153.210.237:80',
    '190.44.84.131:53281',
    '191.253.67.206:8080',
    '192.117.146.110:80',
    '193.108.38.23:80',
    '193.205.4.176:80',
    '193.70.3.144:80',
    '194.44.176.116:8080',
    '195.14.242.39:80',
    '197.254.29.250:65205',
    '197.254.96.42:53281',
    '200.199.23.220:80',
    '200.229.202.72:3128',
    '200.229.202.72:80',
    '200.229.202.72:8080',
    '200.42.45.211:80',
    '201.184.250.170:3128',
    '201.21.45.182:80',
    '201.245.190.38:65301',
    '202.138.127.66:80',
    '202.154.182.42:65301',
    '202.159.36.70:80',
    '202.159.36.70:8080',
    '202.162.198.26:65309',
    '202.169.41.186:8080',
    '202.78.227.33:80',
    '202.79.36.119:8080',
    '203.146.82.253:3128',
    '203.146.82.253:80',
    '203.58.117.34:80',
    '203.74.4.0:80',
    '203.74.4.1:80',
    '203.74.4.2:80',
    '203.74.4.3:80',
    '203.74.4.4:80',
    '203.74.4.5:80',
    '203.74.4.6:80',
    '203.74.4.7:80',
    '204.11.159.178:53281',
    '205.139.16.179:80',
    '208.83.106.105:9999',
    '209.141.61.84:80',
    '209.159.156.199:80',
    '209.198.197.165:80',
    '211.24.107.188:65301',
    '212.1.100.118:53281',
    '212.110.20.141:88',
    '212.126.107.182:65103',
    '212.184.12.11:80',
    '212.192.120.42:8080',
    '212.3.173.22:53281',
    '212.49.84.71:65301',
    '212.83.164.85:80',
    '213.108.201.82:80',
    '213.134.60.20:80',
    '213.149.105.12:80',
    '213.168.210.76:80',
    '217.115.115.249:80',
    '218.15.25.153:808',
    '218.32.94.77:8080',
    '218.50.2.102:8080',
    '219.91.255.179:80',
    '220.244.27.138:3128',
    '222.97.48.191:80',
    '24.38.71.43:80',
    '24.42.167.242:3128',
    '27.131.51.67:443',
    '31.14.40.113:3128',
    '31.42.118.216:53281',
    '31.47.198.61:80',
    '35.154.200.203:80',
    '35.199.36.250:3128',
    '36.66.59.229:65309',
    '36.67.42.123:65103',
    '36.67.48.11:65103',
    '36.67.78.53:53281',
    '36.85.246.175:80',
    '37.59.36.212:88',
    '40.114.14.173:80',
    '41.185.29.39:3128',
    '41.242.90.74:65301',
    '41.78.25.185:3128',
    '41.78.25.186:3128',
    '42.115.88.12:65103',
    '46.218.73.162:80',
    '46.38.52.36:8081',
    '47.74.134.234:80',
    '47.90.87.225:88',
    '50.203.117.22:80',
    '51.254.127.194:8080',
    '51.254.127.194:8081',
    '52.170.210.78:1080',
    '52.170.27.141:1080',
    '52.41.94.5:80',
    '52.50.247.10:80',
    '52.65.157.207:80',
    '54.158.134.115:80',
    '54.233.168.79:80',
    '58.176.46.248:8380',
    '61.135.155.82:443',
    '61.153.108.142:80',
    '61.153.67.110:9999',
    '61.187.251.235:80',
    '61.5.207.102:80',
    '61.91.235.226:8080',
    '62.210.249.233:80',
    '62.210.51.150:80',
    '62.99.77.124:65103',
    '64.237.61.242:80',
    '64.34.21.84:80',
    '66.70.191.5:3128',
    '69.73.167.76:80',
    '72.163.218.146:80',
    '74.118.245.70:80',
    '74.121.141.63:80',
    '78.134.212.173:80',
    '80.1.116.80:80',
    '81.36.128.171:8080',
    '81.88.198.162:53281',
    '81.89.60.26:53281',
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
    '92.38.47.239:80',
    '93.170.108.22:3128',
    '93.188.161.129:80',
    '94.153.172.75:80',
    '94.23.56.95:8080',
    '95.110.189.185:80',
    '95.180.225.7:8080',
    '95.189.123.74:8080',
]


def proxy_sort(p):
    errors = len([x for x in p['results'] if x != 'OK'])
    success = len([x for x in p['results'] if x == 'OK'])
    elapsed = sum(p['elapsed'])
    return (int(errors / 5), elapsed, -success)


def load_proxy():
    try:
        with open('proxy-list.txt', 'r') as fh:
            proxy_temp = json.load(fh)
    except:
        proxy_temp = []

    for proxy in proxy_temp:
        proxy['thread'] = None
        PROXY_LIST[proxy['address']] = proxy

    for addr in PROXIES:
        if addr not in PROXY_LIST:
            PROXY_LIST[addr] = {
                'address': addr,
                'thread': None,
                'results': [],
                'elapsed': [],
            }


def drop_proxy(proxy):
    '''Stop using a proxy'''
    with PROXY_LOCK:
        logger.debug('T-{0:02d}: stop using {1}'.format(
            proxy['thread'], proxy['address']))

        proxy['thread'] = None

        with open('proxy-list.txt', 'w') as fh:
            json.dump(sorted(PROXY_LIST.values(), key=proxy_sort), fh, indent=2)


def get_proxy(thread):
    '''Get the first unused proxy'''
    with PROXY_LOCK:
        for proxy in sorted(PROXY_LIST.values(), key=proxy_sort):
            if proxy['thread'] is None and len([x for x in proxy['results'] if x != 'OK']) < 10:
                proxy['thread'] = thread
                logger.info('T-{0:02d}: now using {1}'.format(
                    thread, proxy['address']))

                with open('proxy-list.txt', 'w') as fh:
                    json.dump(sorted(PROXY_LIST.values(), key=proxy_sort), fh, indent=2)

                return proxy

    return None



def sigint_handler(signum, frame):
    global ENDALL
    ENDALL = True
    logger.info('Ctrl+C')


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

    try:
        req = urllib2.Request(
            url='http://sh.g5e.com/hog_ios/jsonway_android.php',
            data=body, headers=headers)

        if proxy:
            req.set_proxy(proxy['address'], 'http')

        fh = urllib2.urlopen(req, timeout=30.0)

        res = fh.read()

    except (StandardError, httplib.HTTPException), e:
        status = '{0}: {1}'.format(e.__class__.__name__, str(e))
        logger.error('T-{0:02d}: {1}'.format(proxy['thread'], status))
        proxy['results'] = (proxy['results'] + [status])[-10:]
        return None

    try:
        return json.loads(res)
    except:
        return {}


def get_friends(suid, name, proxy):
    logger.debug('T-{0:02d}: Querying friends of {1} ({2})'.format(
        proxy['thread'], name, suid))

    qbody = {
      "serviceName": "GameService",
      "methodName": "GetFriends",
      "parameters": [
        suid,
        [ "Profile.username" ],
        1000,   # maximum number of friends to get
        0,      # start index
        53      # client program version
      ]
    }

    friends = []
    while True:
        # get the list of friends via the assigned proxy
        start_time = time.time()
        resp = http_post(json.dumps(qbody), proxy)
        end_time = time.time()

        if resp is None:    # Communication error
            return False

        proxy['results'] = (proxy['results'] + ['OK'])[-10:]
        proxy['elapsed'] = (proxy['elapsed'] + [end_time - start_time])[-10:]

        if not resp.get('response'):
            break   # no more friends -- next user

        friends += resp['response']

        if len(resp['response']) < 1000:
            break   # no more friends -- next user

        # get the next 1000 friends
        qbody['parameters'][3] += 1000

    logger.debug('T-{0:02d}: Queried friends of {1} ({2}) => {3}'.format(
        proxy['thread'], name, suid, len(friends)))

    RESULT_QUEUE.put((suid, friends), True)

    return True


def send_gifts(suid, name, proxy):
    #XXX dummy request for testing
    '''
    gbody = {
      "serviceName": "GameService",
      "methodName": "SendGift",
      "parameters": [
        GIFTER_SUID,
        suid,
        {
          "colvo": GIFT_COUNT,
          "item_id": GIFT_ID,
          "item_id_random": 68,
          "picture_id": GIFTER_PIC,
          "username": GIFTER_NAME
        },
        int(time.time())
      ]
    }
    '''
    gbody = {
      "serviceName": "GameService",
      "methodName": "GetClientVersion",
      "parameters": [ None ]
    }

    logger.debug('T-{0:02d}: Sending gift to {1} ({2})'.format(
        proxy['thread'], name, suid))

    start_time = time.time()
    resp = http_post(json.dumps(gbody), proxy)
    # {"response":18, "error":false, "profiler":{...}, "version":0, "time":...}
    end_time = time.time()

    if resp is None:
        return False

    proxy['results'] = (proxy['results'] + ['OK'])[-10:]
    proxy['elapsed'] = (proxy['elapsed'] + [end_time - start_time])[-10:]

    result = (resp.get('response', False) != False)

    logger.debug('T-{0:02d}: Sent gift to {1} ({2}) => {3}'.format(
        proxy['thread'], name, suid, result))

    RESULT_QUEUE.put((suid, result), True)

    return True


def ProxyThread(thread):
    logger.info('T-{0:02d}: start'.format(thread))

    # Get the first unused proxy in the list
    proxy = get_proxy(thread)

    if not proxy:
        logger.error('T-{0:02d}: No reliable proxy avairable'.format(thread))
        return

    proxy['results'] = []       # result of recent 10 requests
    proxy['elapsed'] = []       # elapsed time of recent 10 successful requests

    while not ENDALL:
        try:
            req = REQUEST_QUEUE.get(True)
            REQUEST_QUEUE.task_done()
        except Queue.Empty:
            continue

        try:
            (prio, suid, name) = req
        except (TypeError, ValueError):
            continue

        if prio in (0, 1):      # GetFriends request
            if not get_friends(suid, name, proxy):
                REQUEST_QUEUE.put((0, suid, name), True)

        elif prio in (2, 3):    # SendGift request
            if not send_gifts(suid, name, proxy):
                REQUEST_QUEUE.put((2, suid, name), True)

        if (len(proxy['results']) >= 10 and \
            len([x for x in proxy['results'] if x != 'OK']) > 5) or \
            sum(proxy['elapsed']) > 100:
            drop_proxy(proxy)
            proxy = get_proxy(thread)
            if not proxy:
                logger.error('T-{0:02d}: No reliable proxy avairable'.format(thread))
                return

        interval = 10
        for i in range(interval):
            if ENDALL:
                break

            time.sleep(1.0)

    drop_proxy(proxy)
    logger.info('T-{0:02}: done'.format(thread))


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
                REQUEST_QUEUE.put((3, suid, name), False)
                cur.execute('''
                    UPDATE users SET gifted = 0 WHERE suid = :suid;
                ''', {'suid': suid})
                gifts[suid] = name
                added += 1

        except Queue.Full:
            logger.warning('MAIN: task queue full')
            break

    dbh.commit()

    logger.info('MAIN: Added {0} gift tasks'.format(added))

    return added


def add_users(dbh, users, limit=0, distance=None):
    cur = dbh.cursor()
    cur.execute('BEGIN IMMEDIATE TRANSACTION;')

    # Select unfollowed users with the latest activity in the last 7 days
    sql = 'SELECT suid, name, distance FROM users '

    if distance is not None:
        sql += 'WHERE distance = {0}'.format(distance)
    else:
        sql += '''WHERE followed IS NULL
            AND updated > strftime('%s', 'now', '-7 day')
            ORDER BY distance, updated DESC
        '''

        if limit > 0:
            sql += 'LIMIT {0}'.format(limit)

    sql += ';'

    cur.execute(sql)

    added = 0
    for (suid, name, distance) in cur.fetchall():
        try:
            if suid not in users:
                REQUEST_QUEUE.put((1, suid, name), False)
                cur.execute('''
                    UPDATE users SET followed = 0 WHERE suid = :suid;
                ''', {'suid': suid})
                users[suid] = (name, distance)
                added += 1

        except Queue.Full:
            logger.warning('MAIN: task queue full')
            break

    dbh.commit()

    logger.info('MAIN: Added {0} follow tasks'.format(added))

    return added


def process_users(dbh, mode):
    # start task threads
    qthreads = []
    while len(qthreads) < 30:
        th = threading.Thread(target=ProxyThread, args=(len(qthreads)+1,))
        th.start()
        qthreads.append(th)

    more_users = True
    gifts = {}
    users = {}
    distance = 0

    global ENDALL
    while not ENDALL:
        trace()
        if mode == 'users':
            # Add myself and immediate friends to the queue
            if (not users) and (distance in (0, 1)):
                add_users(dbh, users, distance=distance)
                distance += 1

            # Do not add any more friends or gifts
            more_users = False

        if more_users and not ENDALL:
            # Get ungifted users from database
            if len(gifts) < 100:
                new_gifts = add_gifts(dbh, gifts, 100)

                # When not enough ungifted users in database
                if new_gifts < 100 and len(users) < 30:
                    # Add follow user tasks
                    add_users(dbh, users, limit=30)

                    if not users:   # no more un-followed users
                        more_users = False

        trace()
        if not gifts and not users:
            break

        while not ENDALL:
            try:
                (suid, result) = RESULT_QUEUE.get(True, 10)
                RESULT_QUEUE.task_done()
                break
            except Queue.Empty:
                pass
        else:
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

                except StandardError:
                    traceback.print_exc()
                    print json.dumps(friend, indent=2)
                    print json.dumps(users[suid], indent=2)
                    ENTDALL = True
                    break

            if ENDALL:
                break

            trace()
            cur.execute('''
                UPDATE users
                SET followed = strftime('%s', 'now')
                WHERE suid = :suid;
            ''', {'suid': suid})

            trace()
            dbh.commit()

            logger.info('MAIN: {0} ({1}) has {2} friends, {3} new, {4} updated'.format(
                users[suid][0], suid, len(result), added, updated))

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

                logger.info('MAIN: {0} ({1}) has received the gift'.format(
                    gifts[suid], suid))

            del gifts[suid]


    # stop worker threads
    logger.info('Stopping all threads')
    ENDALL = True

    for t in qthreads:
        REQUEST_QUEUE.put(None)

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

    """
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
    """

    dbh.commit()


def main():
    try:
        mode = sys.argv[1]
    except:
        mode = None

    load_proxy()

    signal.signal(signal.SIGINT, sigint_handler)
    try:
        with sqlite3.connect(DATABASE, timeout=30.0) as dbh:
            database_init(dbh)
            process_users(dbh, mode)

    except:
        traceback.print_exc()
        raise

    finally:
        ENDALL = True
        sys.exit(0)


if __name__ == '__main__':
    main()


