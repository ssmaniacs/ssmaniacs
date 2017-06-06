// JSONファイルの動的ロード
function HttpStatus(status) {
  switch (status) {
  case 400: return 'Bad Request';
  case 401: return 'Unauthorixed';
  case 402: return 'Payment Required';
  case 403: return 'Forbidden';
  case 404: return 'Not Found';
  case 405: return 'Method Not Allowed';
  case 406: return 'Not Acceptable';
  case 407: return 'Proxy Authentication Required';
  case 408: return 'Request Time-out';
  case 409: return 'Conflict';
  case 410: return 'Gone';
  case 411: return 'Length Required';
  case 412: return 'Precondition Failed';
  case 413: return 'Request Entity Too Large';
  case 414: return 'Request-URI Too Large';
  case 415: return 'Unsupported Media Type';
  case 416: return 'Requested range not satisfiable';
  case 417: return 'Expectation Failed';
  case 500: return 'Internal Server Error';
  case 501: return 'Not Implemented';
  case 502: return 'Bad Gateway';
  case 503: return 'Service Unavailable';
  case 504: return 'Gateway Time-out';
  case 505: return 'HTTP Version not supported';
  default: return 'Unknown HTTP error';
  }
}


// イメージ情報JSONを読み込む
function loadJSON(path, callback) {
  var xobj;

  try {
    // IEではXMLHttpRequestがうまく動かない（ことがある）
    xobj = new ActiveXObject('MSXML2.XMLHTTP.6.0');
  }
  catch (e) {
    xobj = new XMLHttpRequest();
  }

  try {
    if ('overrideMimeType' in xobj) {
      xobj.overrideMimeType('application/json');
    }

    xobj.open('GET', path, true);

    xobj.onreadystatechange = function(){
      if (xobj.readyState == 4) {
        if (xobj.status == '200' || (location.protocol == 'file:' && xobj.status == '0')) {
          // ドキュメントは見当たらないが、ローカルファイルの場合成功時にstatus=0になることがある
          // とりあえずWin版ChromeとIEではstatus=0. FireFoxではローカルでも200.
          callback(xobj.responseText);
        }
        else {
          var message;

          if (xobj.status) {
            message = xobj.status + ' ' + HttpStatus(xobj.status);
          }

          console.log('XMLHttpRequests.status = ' + xobj.status + ' ' + message);
          callback(new Error(message));
        }
      }
    }

    xobj.send(null);
  }
  catch(e) {
    console.log(e);
    callback(e);
  }
}
