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
//var g5e_url = "http://sh.g5e.com/hog_ios/jsonway_android.php";
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
