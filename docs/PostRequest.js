/*
  Post request to Secret Society Server
*/

// SS client version (as of 2017-10 Halloween update)
var ss_client_version = 54;

// CORS回避用リダイレクトオプション
var redirect_method = 0;
var redirect_prefix = [
  "./redirect.php?",  // 独自PHP経由
  (('https:' == document.location.protocol) ? 'https' : 'http') +
    "://cors-anywhere.herokuapp.com/"  // CORS-Anywhere
];

if (document.location.protocol == 'file:') {
  redirect_prefix.unshift("");	// 直接アクセスを先頭に
}
else {
  redirect_prefix.push("");	// 直接アクセスを末尾に
}

// Secret SocietyサーバのURL
var g5e_url = "https://sh.g5e.com/hog_ios/jsonway_ios.php";
//"http://sh.g5e.com/hog_ios/jsonway_android.php"
//"http://sh.g5e.com/hog_ios/jsonway_mac.php"
//"http://sh.g5e.com/hog_ios/jsonway_win.php"
var url = redirect_prefix[0] + g5e_url;

/*
  リクエストデータをJSONデータとしてPOSTする
  直接 -> PHP -> CORS Anywhere の順で試行
*/
function post_request(reqdata, status, callback)
{
  console.log('Posting request to: ' + url);

  status.innerHTML = '<font color="green">' + message['prepare'] + '...</font>';

  var request = new XMLHttpRequest();

  request.onerror = function() {
    // 通信失敗
    console.log('Request failed (status = ' + this.status + ')');

    if (++redirect_method < redirect_prefix.length) {
      // 次のリダイレクト方法を試す
      url = redirect_prefix[redirect_method] + g5e_url;
      post_request(reqdata, status, callback);
    }
    else {
      // 全部失敗
      status.innerHTML = '<font color="red">' + message['net_error'] + '</font>';
    }
  }

  try {
    request.open('POST', url);
  }
  catch (e) {
    request.onerror();
    return;
  }

  request.onload = function() {
    if (this.status != 200 || this.responseText.substr(0, 5) == '<?php') {
      // HTTPエラーまたは
      // phpの中身が返された => サーバがphp実行をサポートしてない
      this.onerror();
      return;
    }

    console.log('Request succeeded');

    var resp;

    try {
      resp = JSON.parse(this.responseText);
    }
    catch (e) {
      resp = null;
    }

    if (!(resp && 'response' in resp)) {
      status.innerHTML = '<font color="red">' + message['net_error'] + '</font>';
    }
    else if (callback) {
      callback(resp['response']);
    }
  }

  request.onreadystatechange = function () {
    status.innerHTML = '<font color="green">' + message['request'] + '...</font>';
  }

  request.timeout = 60000;
  request.ontimeout = function () {
    status.innerHTML = '<font color="red">' + message['timeout'] + '</font>';
  }

  var postbody = JSON.stringify(reqdata);

  // 以下のヘッダを１つでも設定するとCORS Preflight リクエストが発生する
  // なしでもSSサーバは応答してくれるので省略 (2017/10/27現在)
  /*
  request.setRequestHeader('Content-Type', 'application/json');
  request.setRequestHeader('Accept', 'application/json');
  request.setRequestHeader('X-mytona-fix', '1');

  try {
    // HMTLファイルで CryptoJS の md5.js を読み込んでおくこと
    //<script src='./md5.js'></script>
    var hash = CryptoJS.MD5(postbody);
    request.setRequestHeader('x-content-md5', hash);
  }
  catch (e) {}
  */

  request.send(postbody);
}

/*
  招待コードからUIDを取得する

  1. dummy_uidの友達リストを取得
     -> 友達がいれば全員解除
  2. dummy_uidの待機リストを取得
    -> 待機がいれば全員解除
  3. dummy_uidで招待コードを使用
    -> 相手のUIDを取得
  4. dummy_uidの招待を取り消し
*/

// 招待コード判定用のダミーアカウント（友達のいない（はずの）未使用アカウント）
var dummy_uid = 'suid_30357589';  // Tate

var invite_code = null;
var status_field = null;
var target_callback = null;

function get_uid_from_invite(code, field, callback)
{
  invite_code = code;
  status_field = field;
  target_callback = callback;

  var req = {
    "serviceName": "GameService",
    "methodName": "GetFriendsUids",
    "parameters": [
      dummy_uid, ss_client_version
    ]
  };
  console.log('GetFriendsUids');

  post_request(req, status_field,
    function (resp) { get_friendsuids_done(resp); });
}

// GetFriendsUidsリクエスト完了
var friends = [];
function get_friendsuids_done(resp)
{
  friends = resp;

  if (friends.length) {
    remove_friends(); // 友達がいるので削除
  }
  else {
    get_waitings();   // 友達はいないので待機リストチェック
  }
}

// 友達がいたら解除する
function remove_friends()
{
  if (friends.length) {
    var req = {
      "serviceName": "GameService",
      "methodName": "RemoveFriend",
      "parameters": [
        dummy_uid, friends.shift()
      ]
    };
    console.log('RemoveFriend ' + req['parameters'][1]);

    post_request(req, status_field,
      function (resp) { remove_friends(); });
  }
  else {  // 友達はもういないので待機リストチェック
    get_waitings();
  }
}

// 待機リストをチェックする
function get_waitings()
{
  var req = {
    "serviceName": "GameService",
    "methodName": "GetWaitings",
    "parameters": [
      dummy_uid, ["Profile.username"], ss_client_version
    ]
  };
  console.log('GetWaitings');

  post_request(req, status_field,
    function (resp) { get_waitings_done(resp); });
}

// GetWaitingsリクエストが完了
var waitings = [];
function get_waitings_done(resp)
{
  waitings = [];

  for (var idx in resp['waiting_them']) {
    waitings.push(resp['waiting_them'][idx]['uid']);
  }
  for (var idx in resp['waiting_us']) {
    waitings.push(resp['waiting_us'][idx]['uid']);
  }

  if (waitings.length) {
    remove_waitings();
  }
  else {
    use_invite();
  }
}

// 待機リストのユーザを削除する
function remove_waitings()
{
  if (waitings.length) {
    var req = {
      "serviceName": "GameService",
      "methodName": "DeclineInvite",
      "parameters": [ dummy_uid, waitings.shift() ]
    };
    console.log('DeclineInvite ' + req['parameters'][1]);

    post_request(req, status_field,
      function (resp) { remove_waitings(); });
  }
  else {  // 待機はもういないので招待コード使用
    use_invite();
  }
}

// 招待コードを使用する
function use_invite()
{
  var req = {
    "serviceName": "GameService",
    "methodName": "UseInviteCode",
    "parameters": [ dummy_uid, invite_code, true, true ]
  };
  console.log('UseInviteCode');

  post_request(req, status_field,
    function (resp) { invite_done(resp); });
}

// UseInviteリクエスト完了時に非同期で呼ばれる
function invite_done(resp)
{
  if (resp['result'] != 0) {
    var msg;
    if (resp['result'] == 3) {
      msg = message['code_expired'];  // 招待コードが間違ってるって。古いのかも？
    }
    else if (resp['result'] == 4) {
      msg = message['code_format'];   // 招待コードが間違ってるって。英数字６文字だよ。
    }
    else if (resp['result'] == 5) {
      msg = message['code_waiting'];  // 友達申請済みか、もう友達かも。待機中のリストに" + gifter_name + "がいたら承認して。再登録するならいったん友達削除して。
    }
    else {
      msg = mesasge['code_invite'] + ' (' + resp['result'] + ')';   // 友達申請エラー
    }
    status_field.innerHTML = '<font color="red">' + msg + '</font>';
    return;
  }
  else {
    target_uid = resp['uid'];

    // 招待リクエスト取り消し
    decline_invite();
  }
}

// UseInvite成功後
function decline_invite()
{
  var req = {
    "serviceName": "GameService",
    "methodName": "DeclineInvite",
    "parameters": [ dummy_uid, target_uid ]
  };
  console.log('DeclineInvite ' + target_uid);

  post_request(req, status_field,
    function(resp) { target_callback(target_uid); });
}
