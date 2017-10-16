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
  document.getElementById('peek_status').innerHTML = '';

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

  display_user();
  peek_giftbox();
}

// GetProfilesによるプロファイル取得が成功した
function peek_giftbox()
{
  var req = {
    "serviceName": "GameService",
    "methodName": "GetGifts",
    "parameters": [ userinfo['userid'] ]
  };

  send_request(req, document.getElementById('peek_status'),
    function(resp) { peek_giftbox_done(resp); });
}

// GetInventoryリクエスト完了時に非同期で呼ばれる
function peek_giftbox_done(resp)
{
  var stat = document.getElementById('peek_status')

  var text = '<table border="1" cellpadding="3">' +
    '<tr>' +
    '<th>Nr.</th>' +
    '<th>Name</th>' +
    '<th>Item</th>' +
    '</tr>';

  if (resp.length == 0) {
    text += '<tr><td colspan="3" align="center">No Gift</td></tr>';
  }
  else {
    var num = 0;
    for (var idx in resp) {
      var itemname = itemlist[resp[idx]['item']['item_id']];
      if (!itemname) {
        itemname = 'item-' + resp[idx]['item']['item_id'];
      }
      
      if (resp[idx]['item']['colvo'] > 1) {
        itemname += ' x' + resp[idx]['item']['colvo'];
      }
      
      num += 1
      text += '<tr>' +
        '<td align="right">' + num + '</td>' +
        '<td>' + resp[idx]['item']['username'] + '</td>' +
        '<td>' + itemname + '</td>' +
        '</tr>';
    }
  }
  
  text += '</table>';
  stat.innerHTML = text;
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
