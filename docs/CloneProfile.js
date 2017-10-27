/*
  プロファイルおよびインベントリを別IDのユーザにコピーする
*/
// 招待コード判定用のダミーアカウント（友達のいない未使用アカウント）
var dummy_uid = 'suid_30357589';  // Tate

// 新旧端末のアカウント情報
var userinfo = {
  'old': {},
  'new': {}
};


function get_jobname(job)
{
  if (job in jobname_text) {
    return jobname_text[job];
  }
  else if (job) {
    return message['Unknown'] + "(" + job + ")";
  }
  else {
    return "";
  }
}


// ユーザアカウント情報表示
function display_user(pfx, info)
{
  document.getElementById(pfx + '_uid').innerHTML = 'uid' in info ? info['uid'] : '';
  document.getElementById(pfx + '_dev').innerHTML = 'dev' in info ? info['dev'] : '';
  document.getElementById(pfx + '_nam').innerHTML = 'nam' in info ? info['nam'] : '';
  document.getElementById(pfx + '_job').innerHTML = 'job' in info ? get_jobname(info['job']) : '';
  document.getElementById(pfx + '_lvl').innerHTML = 'lvl' in info ? info['lvl'] : '';
  document.getElementById(pfx + '_exp').innerHTML = 'exp' in info ? info['exp'] : '';
  document.getElementById(pfx + '_qst').innerHTML = 'qst' in info ? info['qst'] : '';

  document.getElementById('clone').disabled = 
    !(userinfo['old']['uid'] && userinfo['old']['profile'] && userinfo['old']['inventory'] &&
    userinfo['new']['uid'] && userinfo['new']['profile'] && userinfo['new']['inventory']);
}

// ユーザアカウント情報確認
function verify_user(pfx)
{
  userinfo[pfx] = {};
  var info = userinfo[pfx];
  var code = document.getElementById(pfx + '_code').value;

  if (code.length < 6) {
    info['uid'] = '<font color="red">' + message['code_error'] + '</font>';
    display_user(pfx, info);
  }
  else if (code.length == 6) { // assume invite code
    // use invite code and get uid
    use_invite(code, pfx, info);
  }
  else {  // assume userid
    info['uid'] = code;
    document.getElementById(pfx + '_uid').innerHTML = code;
    get_profile(pfx, info);
  }
}

// 招待コードを入力して確認ボタンが押された
function use_invite(code, pfx, info)
{
  var req = {
    "serviceName": "GameService",
    "methodName": "UseInviteCode",
    "parameters": [ dummy_uid, code, true, true ]
  };

  post_request(req, document.getElementById(pfx + '_uid'),
    function (resp) { invite_done(pfx, info, resp); });
}

// UseInviteリクエスト完了時に非同期で呼ばれる
function invite_done(pfx, info, resp)
{
  var stat = document.getElementById(pfx + '_uid')

  if (resp['result'] != 0) {
    stat.innerHTML = '<font color="red">' + message['code_error'] + '</font>';
    return;
  }

  info['uid'] = resp['uid'];
  display_user(pfx, info);

  // リクエスト取り消し
  decline_invite(pfx, info);

  // UIDからプロファイル取得
  get_profile(pfx, info);
}

// UseInvite成功後
function decline_invite(pfx, info)
{
  var req = {
    "serviceName": "GameService",
    "methodName": "DeclineInvite",
    "parameters": [ dummy_uid, info['uid'] ]
  };

  post_request(req, document.getElementById(pfx + '_uid'), null);
}

// UseInviteによるUID取得成功後、またはUIDを入力して確認ボタンが押された
function get_profile(pfx, info)
{
  var req = {
    "serviceName": "GameService",
    "methodName": "GetProfiles",
    "parameters": [ [ info['uid'] ], null, 53 ]
  };

  post_request(req, document.getElementById(pfx + '_nam'),
    function(resp) { get_profile_done(pfx, info, resp); });
}

// GetProfilesリクエスト完了時に非同期で呼ばれる
function get_profile_done(pfx, info, resp)
{
  var stat = document.getElementById(pfx + '_nam')
  var profile = resp[0]['data']

  if (!profile) {
    stat.innerHTML = '<font color="red">' + message['net_error'] + '</font>';
    return;
  }

  info['profile'] = profile
  info['nam'] = profile['Profile']['username'];
  info['job'] = profile['Profile']['profession'];
  info['lvl'] = profile['Profile']['level'];
  info['exp'] = profile['Profile']['experience'];

  /*
    idForDeviceからデバイス種別を推定する
    a0d638a586c5fdf4  Android
    C02DN3HWDDR0      Mac
    76B5251E-7CB4-470B-A3EB-F490F3944CB7 iOS
    11216922214024622250186              Win
  */
  var devid = profile['Profile']['idForDevice_vendor'];
  if (/^[0-9a-f]{15,16}$/.test(devid)) {
    info['dev'] = 'Android';
  }
  else if (/^[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}$/.test(devid)) {
    info['dev'] = 'iOS';
  }
  else if (/^[0-9A-Z]{11,12}$/.test(devid)) {
    info['dev'] = 'Mac';
  }
  else if (/^[0-9]{16,}$/.test(devid)) {
    info['dev'] = 'Windows';
  }
  else {
    info['dev'] = message['Unknown'];
  }

  display_user(pfx, info);
  get_inventory(pfx, info);
}

// GetProfilesによるプロファイル取得が成功した
function get_inventory(pfx, info)
{
  var req = {
    "serviceName": "GameService",
    "methodName": "GetInventory",
    "parameters": [ info['uid'] ]
  };

  post_request(req, document.getElementById(pfx + '_qst'),
    function(resp) { get_inventory_done(pfx, info, resp); });
}

// GetInventoryリクエスト完了時に非同期で呼ばれる
function get_inventory_done(pfx, info, resp)
{
  var stat = document.getElementById(pfx + '_qst')

  if (!('Inventory' in resp)) {
    stat.innerHTML = '<font color="red">' + message['net_error'] + '</font>';
    return;
  }

  info['inventory'] = resp;
  info['qst'] = resp['completedQuests']['quest_id'].length;

  display_user(pfx, info);
}

// 複製ボタンが押された
function clone_data()
{
  var stat = document.getElementById('clone_status');

  if (!(userinfo['old']['uid'] && userinfo['old']['profile'] && userinfo['old']['inventory'])) {
    stat.innerHTML = '<font color="red">' + message['need_old'] + '</font>';
    return;
  }

  if (!(userinfo['new']['uid'] && userinfo['new']['profile'] && userinfo['new']['inventory'])) {
    stat.innerHTML = '<font color="red">' + message['need_new'] + '</font>';
    return;
  }

  var info = {};
  info['uid']       = userinfo['new']['uid'];
  info['profile']   = userinfo['old']['profile'];
  info['inventory'] = userinfo['old']['inventory'];

  info['profile']['Profile']['GameCurrentVersion'] = userinfo['new']['profile']['Profile']['GameCurrentVersion'];
  info['profile']['Profile']['Version']            = userinfo['new']['profile']['Profile']['Version'];
  info['profile']['Profile']['idForDevice_ad']     = userinfo['new']['profile']['Profile']['idForDevice_ad'];
  info['profile']['Profile']['idForDevice_vendor'] = userinfo['new']['profile']['Profile']['idForDevice_vendor'];
  info['profile']['Profile']['uid']                = userinfo['new']['profile']['Profile']['uid'];
  info['profile']['Version']                       = userinfo['new']['profile']['Version'];
  
  update_profile(info);
}

/*
  プロファイル更新開始
*/
function update_profile(info)
{
  var req = {
    "serviceName": "GameService",
    "methodName": "UpdateProfile",
    "parameters": [ info['uid'], info['profile'] ]
  };

  post_request(req, document.getElementById('clone_status'),
    function(resp) { update_profile_done(info, resp); });
}

/*
  プロファイル更新完了
*/
function update_profile_done(info, resp)
{
  if (!resp) {
    document.getElementById('clone_status').innerHTML = '<font color="red">' + message['net_error'] + '</font>';
    return;
  }
  update_inventory(info);
}

/*
  インベントリ更新開始
*/
function update_inventory(info)
{
  var req = {
    "serviceName": "GameService",
    "methodName": "UpdateInventory",
    "parameters": [ info['uid'], info['inventory'] ]
  };

  post_request(req, document.getElementById('clone_status'),
    function(resp) { update_inventory_done(info, resp); });
}

/*
  インベントリ更新完了
*/
function update_inventory_done(info, resp)
{
  userinfo['new'] = {};
  userinfo['new']['uid'] = info['uid'];
  document.getElementById('clone_status').innerHTML = '<font color="green">' + message['complete'] + '</font>';

  get_profile('new', userinfo['new']);
}
