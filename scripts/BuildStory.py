#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ts=2 et
import sys
import os
import re
import json
from TextInfo import load_textinfo


def dependency(data, dependee_id, dependant_id):
  if dependee_id not in data:
    data[dependee_id] = {'id': dependee_id}

  dependee = data[dependee_id]

  if dependant_id not in data:
    data[dependant_id] = {'id': dependant_id}

  dependant = data[dependant_id]

  if 'depended_by' not in dependee:
    dependee['depended_by'] = [dependant_id]
  elif dependant_id not in dependee['depended_by']:
    dependee['depended_by'].append(dependant_id)

  if 'depends_on' not in dependant:
    dependant['depends_on'] = [dependee_id]
  elif dependee_id not in dependant['depends_on']:
    dependant['depends_on'].append(dependee_id)



def load_tutinfo(data, basedir, filename, tag):
  with open(os.path.join(basedir, filename), 'r') as fh:
    jdata = json.load(fh)

  for k, v in sorted(jdata['tutorial'].items(), key=lambda x: int(x[0])):
    id_ = '{0}:{1:2d}'.format(tag, int(k.rsplit('_', 1)[-1]))
    title = v.get('window_title')
    body = v.get('window_body')
    avatar = v.get('avatar_id', -1)
    diary = v.get('diary_page_id', -1)

    if body and (avatar or diary):
      id_ = '{0}:{1:2d}'.format(tag, int(body.rsplit('_', 1)[-1]))

      if id_ not in data:
        data[id_] = {'id': id_}

      data[id_]['title'] = title

      if body:
        data[id_]['body'] = body

      if avatar >= 0:
        data[id_]['avatar'] = avatar

      if diary >= 0:
        dependency(data, id_, 'diary:{0:3d}'.format(diary))


def load_quest_diary(data, basedir, filename):
  with open(os.path.join(basedir, filename), 'r') as fh:
    jdata = json.load(fh)

  for d in jdata['dependency']:
    dependency(data, 'quest:{0:6d}'.format(d['QuestId']), 'diary:{0:3d}'.format(d['DiaryPage']))



def load_letters(data, basedir, filename):
  with open(os.path.join(basedir, filename), 'r') as fh:
    jdata = json.load(fh)

  for lt in jdata['letters']:
    l = 'letter:{0:2d}'.format(lt['identifier'])
    v = lt['level']
    q = lt['questDef']
    d = lt['diary_page_id']

    if l not in data:
      data[l] = {'id': l}
 
    if v > 1:
      dependency(data, 'level:{0:3d}'.format(v), l)

    if q >= 0:
      dependency(data, 'quest:{0:6d}'.format(q), l)

    if d >= 0:
      dependency(data, l, 'diary:{0:3d}'.format(d))


def load_comics(data, basedir, filename):
  with open(os.path.join(basedir, filename), 'r') as fh:
    for l in fh:
      m = re.search(r'<comics id="(?P<comic>\d+)" quest_id ="(?P<quest>[-0-9]+)" diary_page_id="(?P<diary>[-0-9]+)" ', l)
      if m:
        c = int(m.group('comic')) + 1
        q = int(m.group('quest'))
        d = int(m.group('diary'))

        if q >= 0 and d>= 0:
          dependency(data, 'quest:{0:6d}'.format(q), 'comic:{0}'.format(c))
          dependency(data, 'comic:{0}'.format(c), 'diary:{0:3d}'.format(d))
          dependency(data, 'quest:{0:6d}'.format(q), 'diary:{0:3d}'.format(d))

        elif q >= 0:
          dependency(data, 'quest:{0:6d}'.format(q), 'comic:{0}'.format(c))

        elif d >= 0:
          dependency(data, 'comic:{0}'.format(c), 'diary:{0:3d}'.format(d))


def load_unlock(data, basedir, filename):
  with open(os.path.join(basedir, filename), 'r') as fh:
    jdata = json.load(fh)

  for scene in jdata['UnlockScenesInfo']:
    dependency(data, 'scene:{0:2d}'.format(scene['scene_id']), 'diary:{0:3d}'.format(scene['diaryPageId']))


def load_collect(data, basedir, filename):
  with open(os.path.join(basedir, filename), 'r') as fh:
    jdata = json.load(fh)

  for v in jdata.values():
    if 'letter_id' in v:
      dependency(data, 'quest:{0:6d}'.format(v['quest_id']), 'letter:{0:2d}'.format(v['letter_id']))


def load_quests(data, basedir, filename):
  with open(os.path.join(basedir, filename), 'r') as fh:
    jdata = json.load(fh)

  for info in jdata['quests'].values():
    qid = 'quest:{0:6d}'.format(info['uid'])

    if qid not in data:
      data[qid] = {'id': qid}

    if info['avatar'] >= 0:
      data[qid]['avatar'] = info['avatar']

    a = info.get('accessLevel', 0)
    if a > 1:
      dependency(data, 'level:{0:3d}'.format(a), qid)

    for s in info.get('sceneDependency', []):
      dependency(data, 'scene:{0:2d}'.format(s), qid)

    for d in info.get('dependency',[]):
      dependency(data, 'quest:{0:6d}'.format(d), qid)

    for l in info.get('letterDependency', []):
      dependency(data, 'letter:{0:2d}'.format(d), qid)

    u = info.get('unlockSceneId', -1)
    if u >= 0:
      dependency(data, qid, 'scene:{0:2d}'.format(u + 1))

    if info.get('type') == 'collectibles':
      dependency(data, qid, 'tut-medal: 1')

    if info.get('social', {}).get('subtype') == 'friend':
      dependency(data, qid, 'tut-friend: 1')


def assign_text(data, text):
  for v in data.values():
    try:
      (type_, id_) = v['id'].split(':')
      id_ = int(id_)

      if type_ == 'comic':
        v['text'] = text['COMICS'][id_]['TEXT']

      elif type_ == 'diary':
        v['name'] = text['DIARY'][id_]['TITLE']
        v['text'] = text['DIARY'][id_]['PAGE']

      elif type_ == 'letter':
        if id_ not in text['LETTER']:
          continue

        v['text'] = text['LETTER'][id_]['TEXT']

      elif type_ == 'quest':
        if id_ not in text['QUEST']:
          continue

        if 'TEXT' not in text['QUEST'][id_]:
          continue

        v['text'] = text['QUEST'][id_]['TEXT']
        v['name'] = text['QUEST'][id_]['NAME']
        v['win'] = text['QUEST'][id_]['WIN']
        if 'HINT' in text['QUEST'][id_]:
          v['hint'] =text['QUEST'][id_]['HINT'] 

      elif type_ == 'scene':
        v['text'] = text['SCENE'][id_]['NAME']

      elif type_.startswith('tut-'):
        if v['body'] in text['TUTORIAL'][0]:
          v['text'] = text['TUTORIAL'][0][v['body']]
          v['name'] = text['TUTORIAL'][0][v['title']]

      elif type_ == 'level':
        v['name'] = 'Level {0}'.format(id_)

      else:
        raise RuntimeError('unknown type')

    except:
      sys.stderr.write(json.dumps(v, indent=2, sort_keys=True))
      sys.stderr.write('\n')
      raise


def main():
  data = {}

  basedir = './1024/properties'

  '''
IDS_LETTER_TEXT_1:For your urgent attention: Your uncle Richard suddenly disappeared under mysterious circumstances. In his will he mentioned you as his only heir. I will let you know the details when we meet in person. Please come to the mansion as soon as possible.&cr;&cr; Richard's personal secretary, Christy.

IDS_TUTORIAL_BODY_2:Welcome to Richard's mansion. Just like Richard, you are vested with the special gift of moving inside magic photographs. Test your abilities by investigating the picture of Venice.

LEVEL2

IDS_TUTORIAL_BODY_13:You are making remarkable progress. Richard was right about you. By the way, he left a letter for you&nbsp;- it's on the table.

IDS_LETTER_TEXT_2:Dear nephew, if you are reading this letter, it means you are already at my mansion. I entrust it to you, along with my seat at the Order. I imagine that you're quite surprised to find out about your magic powers. Don't be afraid of these abilities&nbsp;- direct them into good deeds. Help the less fortunate, and you'll achieve much in the Order of the Explorers. Please accept my sincerest regrets that I can't meet you in person. There are solid reasons for that, as the enemy is near. I must disappear for the benefit of the Order and the world.&cr;Your uncle, Richard.

DS_TUTORIAL_BODY_17:All magic pictures were torn up by Richard, and the pieces were hidden. After investigating Venice, you found a missing piece of the Buddhas Square picture. Try to restore the damaged picture.

UNLOCK Buddha's Square

(IDS_PUZZLE_MOSAIC_DESCRIPTION:Move and connect puzzle pieces in order to complete a picture. Double-tap pieces to rotate them.)

IDS_TUTORIAL_BODY_20:Great, you did it! Now, the Buddha's Square picture is available for investigation. In order to find Richard's traces you need to restore all his pictures. In the meantime, meet Alfred the butler.

IDS_FIRST_INTRODUCTION_PERSON_ALFRED:I'm glad to see you! I'm Alfred the butler, and I look after this house. I guess you were quite surprised to discover your magical abilities? Don't worry, Richard also was confused at first.

IDS_QUEST_TEXT_11:Welcome to your mansion. Master Richard was a&nbsp;fine supervisor, and I&nbsp;trust you inherited his best personal qualities as well as his magical powers. I'm afraid I&nbsp;accidentally knocked a&nbsp;piggy bank off the shelf the other day while dusting. I&nbsp;collected all the scattered coins, except for one antique coin I&nbsp;couldn't locate. Could you find it, so I&nbsp;can put it back?

IDS_QUEST_WIN_11:Fantastic! I'll go place this antique coin in the piggy bank right away.

IDS_TUTORIAL_BODY_32:Congratulations! You have completed the tutorial and are now a full-fledged member of the Order of Explorers. You can share this great news with your friends.

====
Diary 0..5
IDS_QUEST_TEXT_12:I'm afraid I&nbsp;lost my lucky coin while working around the mansion. Could you find it for me?

  '''
  dependency(data, 'level:  1', 'scene: 3')         # initial state = level 1, scene 3
  dependency(data, 'scene: 3', 'letter: 1')         # IDS_LETTER_TEXT_1
  dependency(data, 'letter: 1', 'tut-start: 2')     # IDS_TUTORIAL_BODY_2
  dependency(data, 'tut-start: 2', 'level: 2')      # reaches level 2 after the tutorial
  dependency(data, 'level: 2', 'tut-start:13')      # IDS_TUTORIAL_BODY_13
  dependency(data, 'tut-start:13', 'letter: 2')     # IDS_LETTER_TEXT_1
  dependency(data, 'letter: 2', 'tut-start:17')     # IDS_TUTORIAL_BODY_17
  dependency(data, 'tut-start:17', 'tut-start:20')  # IDS_TUTORIAL_BODY_20
  dependency(data, 'tut-start:17', 'scene: 2')      # Buddha unlocked
#  dependency(data, 'tut-start:20', 'avater: 4')     # IDS_FIRST_INTRODUCTION_PERSON_ALFRED
  dependency(data, 'quest:    11', 'tut-start:32')  # IDS_TUTORIAL_BODY_32
  dependency(data, 'avatar: 2', 'diary:  1')        # christy
  dependency(data, 'avatar: 4', 'diary:  4')        # alfred
  dependency(data, 'avatar: 5', 'diary: 10')        # howard
  dependency(data, 'avatar: 3', 'diary: 11')        # vincent
  dependency(data, 'avatar: 1', 'diary: 14')        # john doe
  dependency(data, 'avatar: 6', 'diary: 18')        # may g
  dependency(data, 'avatar: 7', 'diary: 33')        # rosalind
  dependency(data, 'avatar: 9', 'diary: 34')        # danny
  dependency(data, 'avatar: 8', 'diary: 35')        # ghost
  dependency(data, 'avatar:10', 'diary: 59')        # lewis
  dependency(data, 'avatar:11', 'diary: 62')        # michael
  dependency(data, 'avatar:12', 'diary: 81')        # alice
  dependency(data, 'avatar:13', 'diary: 86')        # steffan
  dependency(data, 'avatar:14', 'diary: 92')        # steffan
  dependency(data, 'avatar:15', 'diary:101')        # jacqueline
  dependency(data, 'avatar:16', 'diary:118')        # archivist
  dependency(data, 'avatar:17', 'diary:153')        # dietrich
  dependency(data, 'avatar:18', 'diary:232')        # goldsmith

  # 'diary:  8' - anomaly
  # 'diary: 16' - mysterious shadoow
  # 'diary: 20' - strange casket
  # 'diary: 21' - first explorer
  # 'diary: 24' - the exiled one
  # 'diary: 27' - erased memories
  # 'diary: 28' - artifact
  # 'diary: 31' - spy
  # 'diary: 45' - magical photo
  # 'diary: 46' - possession of maklar
  # 'diary: 95' - picnic
  '''
  #dependency(data, 'quest:300020', 'scene:   ')     # holiday picnic photo?
  #dependency(data, 'quest:300031', 'scene: 29')     # observation deck (q:300032)
  #dependency(data, 'quest:300034', 'scene: 30')     # banquet hall (q:300033)
  #dependency(data, 'quest:300036', 'scene: 31')     # Spooky yard (q:300035)
  #dependency(data, 'quest:300038', 'scene: 32')     # wonder shop (q:300037)
  #dependency(data, 'quest:300040', 'scene: 33')     # mountain resort (q:300039)
  #dependency(data, 'quest:300042', 'scene: 34')     # spring festival (q:300041)
  #dependency(data, 'quest:300046', 'scene: 36')     # camping site (q:300044)
  #dependency(data, 'quest:300047', 'scene: 37')     # tropical evening (q:300045)
  #dependency(data, 'quest:300050', 'scene: 39')     # haunted attraction (q:300049)
  #dependency(data, 'quest:300051', 'scene: 38')     # farm (q:300048)
  #dependency(data, 'quest:300056', 'scene: 42')     # festive dinner (q:300054)
  #dependency(data, 'quest:300061', 'scene: 41')     # luxury express (q:300053)
  #dependency(data, 'quest:300062', 'scene: 44')     # orangery (q:300058)
  #dependency(data, 'quest:300063', 'scene: 45')     # tea corner (q:300059)
  '''

  for i in (1, 2):
    dependency(data, 'tut-medal:{0:>2d}'.format(i), 'tut-medal:{0:>2d}'.format(i+1))

  for i in range(1, 8):
    dependency(data, 'tut-friend:{0:>2d}'.format(i), 'tut-friend:{0:>2d}'.format(i+1))

  load_letters(data, basedir, 'data_letters.xml')
  load_tutinfo(data, basedir, 'collectibles_tutorial.xml', 'tut-medal')
  load_tutinfo(data, basedir, 'friend_tutorial.xml', 'tut-friend')
  load_tutinfo(data, basedir, 'tutorial.xml', 'tut-start')
  load_quest_diary(data, basedir, 'diary_page_dependency.json')
  load_comics(data, basedir, 'data_comics.xml')
  load_unlock(data, basedir, 'data_balance.json')
  load_collect(data, basedir, 'collectibles.json')
  load_quests(data, basedir, 'quests.xml')

  for i in ('quest:10894741', 'tut-start: 1', 'tut-start:25', 'tut-start:26', 'tut-start:29', 'tut-start:30', 'tut-start:31'):
    data[i]['done'] = True

  text = load_textinfo('.', 'en')

  for i in text['DIARY'].keys():
    key = 'diary:{0:>3d}'.format(i)
    if key not in data:
      data[key] = {'id': key}

  for i in text['LETTER'].keys():
    key = 'letter:{0:>2d}'.format(i)
    if key not in data:
      data[key] = {'id': key}

  '''
  for i in text['QUEST'].keys():
    key = 'quest:{0:>6d}'.format(i)
    if key not in data:
      data[key] = {'id': key}
  '''

  assign_text(data, text)

  for (k, v) in sorted(data.items()):
    #if 'depends_on' in v or v.get('done'):
    #  continue

    print json.dumps(v, indent=2, sort_keys=True, ensure_ascii=False).encode('utf-8')

  #print json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False).encode('utf-8')
  # ['ITEM', 'PHENOMEN', 'LEVEL', 'PUZZLE', 'SCENE', 'PERSON', 'QUEST', 'DIARY', 'LETTER', 'SCENETYPE']


if __name__ == '__main__':
  main()
