var redirect_method = 0;
var redirect_php = "./redirect.php?";
var cors_anywhere = "http://cors-anywhere.herokuapp.com/";

// Secret SocietyサーバのURL
var g5e_url = "http://sh.g5e.com/hog_ios/jsonway_android.php";
var url = g5e_url;

// 招待コード判定用のダミーアカウント（友達のいない未使用アカウント）
var dummy_uid = 'suid_30357589';  // Tate

// アカウント情報
var userinfo = {};


window.onload = function ()
{
  var result = new Array();
  var allcookies = document.cookie;
  if (allcookies != '') {
     var cookies = allcookies.split('; ');

     for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i].split('=');
        result[cookie[0]] = decodeURIComponent(cookie[1]);
     }
  }

  if (result['userid']) {
    document.getElementById('userinput').value = result['userid'];
    verify_user();
  }
}


function get_jobname(job)
{
  if (!job) {
    return "";
  }
  else if (job == 2) {
    return message['Merchant'];
  }
  else if (job == 4) {
    return message['Sage'];
  }
  else if (job == 8) {
    return message['Sleuth'];
  }
  else if (job == 16) {
    return message['Magician'];
  }
  else {
    return message['Unknown'] + "(" + job + ")";
  }
}


// ユーザアカウント情報表示
function display_user()
{
  document.getElementById('userid'    ).innerHTML = 'userid'     in userinfo ? userinfo['userid'] : '';
  document.getElementById('username'  ).innerHTML = 'username'   in userinfo ? userinfo['username'] : '';
  document.getElementById('profession').innerHTML = 'profession' in userinfo ? get_jobname(userinfo['profession']) : '';
  document.getElementById('level'     ).innerHTML = 'level'      in userinfo ? userinfo['level'] : '';
}


// ユーザアカウント情報確認
function verify_user()
{
  userinfo = {};
  var code = document.getElementById('userinput').value;

  document.getElementById('userid'    ).innerHTML = '';
  document.getElementById('username'  ).innerHTML = '';
  document.getElementById('profession').innerHTML = '';
  document.getElementById('level'     ).innerHTML = '';
  document.getElementById('comm_status').innerHTML = '';

  if (code.length < 6) {
    userinfo['userid'] = '<font color="red">' + message['code_error'] + '</font>';
    display_user();
  }
  else if (code.length == 6) {  // assume invite code
    use_invite(code);           // use invite code and get uid
  }
  else {  // assume userid
    userinfo['userid'] = code;
    document.getElementById('userid').innerHTML = code;
    get_profile();
  }
}

// 招待コードを入力して確認ボタンが押された
function use_invite(code)
{
  var req = {
    "serviceName": "GameService",
    "methodName": "UseInviteCode",
    "parameters": [ dummy_uid, code, true, true ]
  };

  send_request(req, document.getElementById('userid'),
    function (resp) { invite_done(resp); });
}

// UseInviteリクエスト完了時に非同期で呼ばれる
function invite_done(resp)
{
  var stat = document.getElementById('userid')

  if (resp['result'] != 0) {
    stat.innerHTML = '<font color="red">' + message['code_error'] + '</font>';
    return;
  }

  userinfo['userid'] = resp['uid'];
  document.getElementById('userinput').value = resp['uid'];

  // 招待リクエスト取り消し
  decline_invite();
}

// UseInvite成功後
function decline_invite()
{
  var req = {
    "serviceName": "GameService",
    "methodName": "DeclineInvite",
    "parameters": [ dummy_uid, userinfo['userid'] ]
  };

  send_request(req, document.getElementById('userid'), 
    function(resp) { get_profile(); });
}

// UseInviteによるUID取得成功後、またはUIDを入力して確認ボタンが押された
function get_profile()
{
  var req = {
    "serviceName": "GameService",
    "methodName": "GetProfiles",
    "parameters": [ [ userinfo['userid'] ], [ "Profile" ], 53 ]
  };

  send_request(req, document.getElementById('username'),
    function(resp) { get_profile_done(resp); });
}

// GetProfilesリクエスト完了時に非同期で呼ばれる
function get_profile_done(resp)
{
  var stat = document.getElementById('username')
  var profile = resp[0]['data']

  if (!profile) {
    stat.innerHTML = '<font color="red">' + message['net_error'] + '</font>';
    return;
  }

  userinfo['username'] = profile['Profile']['username'];
  userinfo['profession'] = profile['Profile']['profession'];
  userinfo['level'] = profile['Profile']['level'];

  // 無期限cookieを格納
  document.cookie = "userid=" + userinfo['userid'] + "; expires=Tue, 19 Jan 2038 03:14:07 GMT";

  // ユーザ情報を表示
  display_user();
}

// ギフト参照ボタンが押された
function peek_giftbox()
{
  var req = {
    "serviceName": "GameService",
    "methodName": "GetGifts",
    "parameters": [ userinfo['userid'] ]
  };

  document.getElementById('result').innerHTML = '';

  send_request(req, document.getElementById('comm_status'),
    function(resp) { peek_giftbox_done(resp); });
}

// GetGiftsリクエスト完了時に非同期で呼ばれる
function peek_giftbox_done(resp)
{
  var status = document.getElementById('comm_status');
  var result = document.getElementById('result');

  status.innerHTML = message['gifts_1'] + resp.length + message['gifts_2'];
  result.innerHTML = message['generating'];
  setTimeout(gifts_list, 0, resp);
}

// 友達リストボタンが押された
var friends = [];
function get_friends(start)
{
  if (start == 0) {
    friends = [];
    document.getElementById('result').innerHTML = '';
  }

  var req = {
    "serviceName": "GameService",
    "methodName": "GetFriends",
    "parameters": [
      userinfo['userid'],
      [
        "Profile.username",
        "Profile.picture_id",
        "Profile.profession",
        "Profile.level",
        "Profile.experience",
        "Profile.friendsCount",
        "Profile.reputation",
        "FB_pic",
        "FB_name",
      ],
      150,
      start,
      53
    ]
  };

  send_request(req, document.getElementById('comm_status'),
    function(resp) { get_friends_done(resp); });
}

// GetFriendsリクエスト完了時に非同期で呼ばれる
function get_friends_done(resp)
{
  var status = document.getElementById('comm_status')
  var result = document.getElementById('result')

  for (var idx in resp) {
    var f = resp[idx];
    var fdata = {
      'name': f['data']['Profile']['username'],
      'picture': f['data']['Profile']['picture_id'],
      'profession': f['data']['Profile']['profession'],
      'FBname': f['data']['FB_name'],
      'FBpic': f['data']['FB_pic'],
      'level': f['data']['Profile']['level'],
      'experience': f['data']['Profile']['experience'],
      'friends': f['data']['Profile']['friendsCount'],
      'reputation': f['data']['Profile']['reputation'],
      'update': f['last_update']
    };
    if (!fdata['name']) {
      fdata['name'] = ' (' + f['uid'] + ')';
    }
    friends.push(fdata);
    //console.log(f['uid'], f['data']['Profile']['username']);
  }

  result.innerHTML = message['friends_1'] + friends.length + message['friends_2'];

  if (resp.length < 150) {
    status.innerHTML = result.innerHTML;
    result.innerHTML = message['generating'];
    setTimeout(friends_list, 0);
  }
  else {
    get_friends(friends.length);
  }
}

// 所持品チェックボタンが押された
function get_inventory()
{
  var req = {
    "serviceName": "GameService",
    "methodName": "GetInventory",
    "parameters": [ userinfo['userid'] ]
  };

  document.getElementById('result').innerHTML = '';

  send_request(req, document.getElementById('comm_status'),
    function(resp) { get_inventory_done(resp); });
}

// GetGiftsリクエスト完了時に非同期で呼ばれる
function get_inventory_done(resp)
{
  var status = document.getElementById('comm_status');
  var result = document.getElementById('result');

  status.innerHTML = '';
  result.innerHTML = message['generating'];
  setTimeout(inventory_list, 0, resp['Inventory']);
}

// 進行状況チェックボタンが押された
var sceneinfo = null;

function get_progress()
{
  if (!sceneinfo) {
    loadJSON(scene_info, function(resp) {
      sceneinfo = JSON.parse(resp);
      get_progress();
    });
    return;
  }

  var req = {
    "serviceName": "GameService",
    "methodName": "GetProfiles",
    "parameters": [[userinfo['userid']], null, 53]
  };

  document.getElementById('result').innerHTML = '';

  send_request(req, document.getElementById('comm_status'),
    function(resp) { get_progress_done(resp); });
}

// GetProfilesリクエスト完了時に非同期で呼ばれる
function get_progress_done(resp)
{
  var status = document.getElementById('comm_status');
  var result = document.getElementById('result');

  status.innerHTML = '';
  result.innerHTML = message['generating'];
  setTimeout(progress_list, 0, resp[0]['data']);
}


// イメージをロード
var default_img = 'img/pic_1.jpg';

function select_image(imgurl)
{
  // デフォルトURLを候補リストに追加
  if (imgurl.length == 0 || imgurl[imgurl.length - 1] != default_img) {
    imgurl.push(default_img);
  }

  // イメージオブジェクトを作成
  // Imageコンストラクタのサイズ指定だとMac Safariがサイズ変更してくれない
  var img = new Image();
  img.width = 50;
  img.height = 50;

  // ロードエラー時に次の候補URLで試行
  img.onerror = function() {
    console.log(this.src + ' load failed');
    if (imgurl.length) {
      this.src = imgurl.shift();
    }
  }

  img.src = imgurl.shift();
  return img;
}

// ギフトリストテーブルを生成
function gifts_list(gifts)
{
  var result = document.getElementById('result');

  var tbl = document.createElement('table');
  tbl.border = 1;

  var row = tbl.insertRow(0);
  gifts_header.forEach(function(val) {
    var th = document.createElement('th');
    th.innerHTML = val;
    row.appendChild(th);
  });

  var cell;

  if (gifts.length == 0) {
    row = tbl.insertRow(-1);
    cell = row.insertCell(-1);
    cell.colSpan = gifts_header.length;
    cell.style.textAlign = 'center';
    cell.style.padding = '3px';
    cell.innerHTML = 'No Gift';
  }
  else {
    for (var idx in gifts) {
      var item = gifts[idx]['item'];
      var row = tbl.insertRow(-1);

      var cell = row.insertCell(-1);
      cell.style.textAlign = 'right';
      cell.style.padding = '3px';
      cell.innerHTML = +idx + 1;

      cell = row.insertCell(-1);
      cell.style.textAlign = 'center';

      var imgurl = [];

      if (item['photo'] && item['photo'] != 'silhouette') {
        imgurl.push(item['photo']);
      }

      if (item['picture_id'] && item['picture_id'] >= 1) {
        imgurl.push('img/pic_' + item['picture_id'] + '.jpg');
      }
      else {
        imgurl.push(default_img);
      }
      cell.appendChild(select_image(imgurl));

      cell = row.insertCell(-1);
      cell.style.padding = '3px';
      cell.innerHTML = item['username'];

      var itemname = itemlist[item['item_id']];
      if (!itemname) {
        itemname = 'item-' + item['item_id'];
      }

      if (item['colvo'] > 1) {
        itemname += ' x' + item['colvo'];
      }

      cell = row.insertCell(-1);
      cell.style.padding = '3px';
      cell.innerHTML = itemname;
    }
  }
  
  result.innerHTML = '';
  result.appendChild(tbl);
}

//  友達リストテーブルを生成
function friends_list()
{
  var result = document.getElementById('result');

  var tbl = document.createElement('table');
  tbl.border = 1;

  var row = tbl.insertRow(0);
  friends_header.forEach(function(val) {
    var th = document.createElement('th');
    th.innerHTML = val;
    row.appendChild(th);
  });

  if (friends.length == 0) {
    row = tbl.insertRow(-1);
    var cell = row.insertCell(-1);
    cell.colSpan = friends_header.length;
    cell.style.textAlign = 'center';
    cell.style.padding = '3px';
    cell.innerHTML = 'No Friend';
    result.innerHTML = '';
    result.appendChild(tbl);
    return;
  }

  friends.sort(function(a, b) {
    if (a['name'] > b['name']) return 1;
    if (a['name'] < b['name']) return -1;
    return 0;
  });

  for (var idx in friends) {
    var f = friends[idx];
    var row = tbl.insertRow(-1);

    var cell = row.insertCell(-1);
    cell.style.textAlign = 'right';
    cell.style.padding = '3px';
    cell.innerHTML = +idx + 1;

    cell = row.insertCell(-1);
    cell.style.textAlign = 'center';

    var imgurl = [];
    if (f['FBpic'] && f['FBpic'] != 'silhouette') {
      imgurl.push(f['FBpic']);
    }
    if (f['picture'] && f['picture'] >= 1) {
      imgurl.push('img/pic_' + f['picture'] + '.jpg');
    }
    else {
      imgurl.push(default_img);
    }
    cell.appendChild(select_image(imgurl));

    cell = row.insertCell(-1);
    cell.style.padding = '3px';
    cell.innerHTML = f['name'];

    cell = row.insertCell(-1);
    cell.style.padding = '3px';
    if (f['FBname']) {
      cell.innerHTML = f['FBname'];
    }

    cell = row.insertCell(-1);
    cell.style.padding = '3px';
    cell.innerHTML = get_jobname(f['profession']);

    cell = row.insertCell(-1);
    cell.style.textAlign = 'right';
    cell.style.padding = '3px';
    cell.innerHTML = f['level'];

    cell = row.insertCell(-1);
    cell.style.textAlign = 'right';
    cell.style.padding = '3px';
    cell.innerHTML = f['experience'];

    cell = row.insertCell(-1);
    cell.style.textAlign = 'right';
    cell.style.padding = '3px';
    cell.innerHTML = f['friends'];

    cell = row.insertCell(-1);
    cell.style.textAlign = 'right';
    cell.style.padding = '3px';
    cell.innerHTML = f['reputation'];

    var ts = new Date( f['update'] * 1000 );

    cell = row.insertCell(-1);
    cell.style.padding = '3px';
    cell.innerHTML =
    [
      ts.getFullYear(),
      ts.getMonth() + 1,
      ts.getDate()
    ].join( '/' ) + ' ' + ts.toLocaleTimeString();
  }

  result.innerHTML = '';
  result.appendChild(tbl);
}

// 持ち物リストテーブルを生成
function inventory_list(inventory)
{
  var result = document.getElementById('result');

  var tbl = document.createElement('table');
  tbl.border = 1;

  var row = tbl.insertRow(0);
  inventory_header.forEach(function(val) {
    var th = document.createElement('th');
    th.innerHTML = val;
    row.appendChild(th);
  });

  var cell;

  if (inventory['item_id'].length == 0) {
    row = tbl.insertRow(-1);
    cell = row.insertCell(-1);
    cell.colSpan = inventory_header.length;
    cell.style.textAlign = 'center';
    cell.style.padding = '3px';
    cell.innerHTML = 'No Item';
  }
  else {
    for (var idx in inventory['item_id']) {
      var itemid = inventory['item_id'][idx];
      var itemcount = inventory['item_count'][idx];
      var itemname = itemlist[itemid];
      if (!itemname) {
        itemname = 'item-' + itemid;
      }

      var row = tbl.insertRow(-1);

      var cell = row.insertCell(-1);
      cell.style.textAlign = 'right';
      cell.style.padding = '3px';
      cell.innerHTML = itemid;

      cell = row.insertCell(-1);
      cell.style.padding = '3px';
      cell.innerHTML = itemname;

      cell = row.insertCell(-1);
      cell.style.textAlign = 'right';
      cell.style.padding = '3px';
      cell.innerHTML = itemcount;
    }
  }
  
  result.innerHTML = '';
  result.appendChild(tbl);
}

var progress_rate = {
  1:  [5, 8, 12, 25, 100, 200, 400, 600, 800],
  2:  [4, 7, 11, 25, 100, 200, 400, 600, 800],
  3:  [3, 6, 10, 25, 100, 200, 400, 600, 800],
  4:  [5, 8, 12, 25, 100, 200, 400, 600, 800],
  5:  [5, 9, 13, 25, 100, 200, 400, 600, 800],
  6:  [5, 9, 13, 25, 100, 200, 400, 600, 800],
  7:  [5, 10, 14, 25, 100, 200, 400, 600, 800],
  8:  [5, 10, 14, 25, 100, 200, 400, 600, 800],
  9:  [5, 11, 14, 25, 100, 200, 400, 600, 800],
  10: [5, 12, 15, 25, 100, 200, 400, 600, 800],
  11: [5, 7, 11, 25, 100, 200, 400, 600, 800],
  12: [5, 12, 15, 25, 100, 200, 400, 600, 800],
  13: [6, 13, 16, 33, 100, 200, 400, 600, 800],
  14: [6, 13, 16, 33, 100, 200, 400, 600, 800],
  15: [8, 18, 25, 40, 100, 200, 400, 600, 800],
  16: [8, 18, 25, 40, 100, 200, 400, 600, 800],
  17: [10, 18, 40, 40, 100, 200, 400, 600, 800],
  18: [10, 18, 25, 40, 100, 200, 400, 600, 800],
  19: [5, 8, 12, 25, 100, 200, 400, 600, 800],
  20: [5, 8, 12, 25, 100, 200, 400, 600, 800],
  21: [5, 8, 12, 25, 100, 200, 400, 600, 800],
  22: [10, 18, 25, 40, 100, 200, 400, 600, 800],
  23: [10, 18, 25, 40, 100, 200, 400, 600, 800],
  24: [10, 18, 25, 40, 100, 200, 400, 600, 800],
  25: [5, 8, 12, 25, 100, 200, 400, 600, 800],
  26: [10, 18, 25, 40, 100, 200, 400, 600, 800],
  27: [5, 8, 12, 25, 100, 200, 400, 600, 800],
  28: [10, 18, 25, 40, 100, 200, 400, 600, 800],
  29: [10, 18, 25, 40, 100, 200, 400, 600, 800],
  30: [10, 18, 25, 40, 100, 200, 400, 600, 800],
  31: [10, 18, 25, 40, 100, 200, 400, 600, 800],
  32: [10, 18, 25, 40, 100, 200, 400, 600, 800],
  33: [10, 18, 25, 40, 100, 200, 400, 600, 800],
  34: [10, 18, 25, 40, 100, 200, 400, 600, 800],
  35: [10, 18, 25, 40, 100, 200, 400, 600, 800],
  36: [10, 18, 25, 40, 100, 200, 400, 600, 800],
  37: [10, 18, 25, 40, 100, 200, 400, 600, 800],
  38: [10, 18, 25, 40, 100, 200, 400, 600, 800],
  39: [10, 18, 25, 40, 100, 200, 400, 600, 800],
  40: [10, 18, 25, 40, 100, 200, 400, 600, 800],
  41: [10, 18, 25, 40, 100, 200, 400, 600, 800],
  42: [10, 18, 25, 40, 100, 200, 400, 600, 800],
  43: [10, 18, 25, 40, 100, 200, 400, 600, 800],
  44: [10, 18, 25, 40, 100, 200, 400, 600, 800],
  45: [10, 18, 25, 40, 100, 200, 400, 600, 800],
  46: [10, 18, 25, 40, 100, 200, 400, 600, 800],
  47: [10, 18, 25, 40, 100, 200, 400, 600, 800],
  48: [10, 18, 25, 40, 100, 200, 400, 600, 800],
  49: [10, 18, 25, 40, 100, 200, 400, 600, 800],
  50: [10, 18, 25, 40, 100, 200, 400, 600, 800],
  51: [10, 18, 25, 40, 100, 200, 400, 600, 800],
  52: [10, 18, 25, 40, 100, 200, 400, 600, 800],
  53: [10, 18, 25, 40, 100, 200, 400, 600, 800],
  54: [10, 18, 25, 40, 100, 200, 400, 600, 800],
  55: [10, 18, 25, 40, 100, 200, 400, 600, 800],
  56: [5, 8, 12, 25, 100, 200, 400, 600, 800],
  57: [5, 8, 12, 25, 100, 200, 400, 600, 800],
  58: [10, 18, 25, 40, 100, 200, 400, 600, 800]
};

//  進行状況テーブルを生成
function progress_list(data)
{
  var result = document.getElementById('result');

  var scenedata = {};
  for (var idx in data['scenelevel']['scene_id']) {
    scenedata[data['scenelevel']['scene_id'][idx]] = {'level': data['scenelevel']['level'][idx]};
  }
  
  if (data['scenephenomens'] && 'scene_id' in data['scenephenomens']) {
    for (var idx in data['scenephenomens']['scene_id']) {
      scenedata[data['scenephenomens']['scene_id'][idx]]['phenom'] = data['scenephenomens']['type'][idx];
    }
  }

  for (var idx in data['sceneprogress']['scene_id']) {
    scenedata[data['sceneprogress']['scene_id'][idx]]['progress'] = data['sceneprogress']['progress'][idx];
  }

  for (var idx in data['scenesUnlocked']['scene_id']) {
    scenedata[data['scenesUnlocked']['scene_id'][idx]]['unlock'] = data['scenesUnlocked']['unlocked'][idx];
  }

  for (var idx in data['scenetypes']['scene_id']) {
    scenedata[data['scenetypes']['scene_id'][idx]]['mode'] = data['scenetypes']['type'][idx];
  }

  var tbl = document.createElement('table');
  tbl.border = 1;

  var row = tbl.insertRow(0);
  progress_header.forEach(function(val) {
    var th = document.createElement('th');
    th.innerHTML = val;
    row.appendChild(th);
  });

  for (var idx in data['scenelevel']['scene_id']) {
    var sceneid = data['scenelevel']['scene_id'][idx];
    if (idx == 0 || sceneid <= 0) {
      continue;
    }
    var scene = scenedata[sceneid];
    var leveltext;
    var modetext;
    var progtext;
    if (scene['unlock']) {
      leveltext = sceneinfo['levels'][scene['level']];

      if (scene['phenom']) {
        modetext = phenom_text[scene['phenom']];
      }
      else {
        modetext = mode_text[scene['mode']];
      }

      progtext = (parseInt(scene['progress'] * 1000 / progress_rate[sceneid][scene['level']]) / 10) + '%' +
        ' (' + scene['progress'] + '/' + progress_rate[sceneid][scene['level']] + ')';
    }
    else {
      leveltext = 'Locked';
      modetext = '-';
      progtext = '-';
    }

    var row = tbl.insertRow(-1);

    var cell = row.insertCell(-1);
    cell.style.textAlign = 'right';
    cell.style.padding = '3px';
    cell.innerHTML = sceneid;

    cell = row.insertCell(-1);
    cell.style.padding = '3px';
    cell.innerHTML = sceneinfo['scenes'][sceneid];

    cell = row.insertCell(-1);
    cell.style.padding = '3px';
    cell.innerHTML = leveltext;

    cell = row.insertCell(-1);
    cell.style.padding = '3px';
    cell.innerHTML = modetext;

    cell = row.insertCell(-1);
    cell.style.padding = '3px';
    cell.style.textAlign = 'right';
    cell.innerHTML = progtext;
  }
  
  result.innerHTML = '';
  result.appendChild(tbl);
}


function send_request(req, stat, done)
{

  var data = JSON.stringify(req);

  stat.innerHTML = '<font color="green">' + message['prepare'] + '...</font>';

  var running = false;

  var request = new XMLHttpRequest();
  request.open('POST', url);
  request.onreadystatechange = function () {
    running = true;
    if (request.readyState != 4) {
        stat.innerHTML = '<font color="green">' + message['request'] + '...</font>';
    }
    else if (request.status != 200) {
        if (redirect_method == 0) {       // 直接接続失敗
          redirect_method = 1;            // redirect.phpで試す
          url = redirect_php + g5e_url;
          send_request(req, stat, done);
        }
        else if (redirect_method == 1) {  // redirect.php失敗
          redirect_method = 2;            // CORS-Anywhereを試す
          url = cors_anywhere + g5e_url;
          send_request(req, stat, done);
        }
        else {                            // 全部失敗
          stat.innerHTML = '<font color="red">' + message['net_error'] + '</font>';
        }
    }
    else {
      var resp = JSON.parse(request.responseText);

      if (resp['error']) {
        stat.innerHTML = '<font color="red">' + message['net_error'] + '</font>';
      }
      else if (done) {
        done(resp['response']);
      }
    }
  };
  request.setRequestHeader('Content-Type', 'application/json');
  request.send(data);
  setTimeout(
    function () {
      if (!running) {
        stat.innerHTML = '<font color="red">' + message['timeout'] + '</font>';
      }
    }, 60000
  );
}
