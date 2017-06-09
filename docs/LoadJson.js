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
          var message = xobj.status + ' ' + xobj.statusText;
          console.log('XMLHttpRequests.status = ' + message);
          callback(new Error(message));
        }
      }
    }

    xobj.send(null);
  }
  catch(e) {
    // HTTPエラー時にonreadystatechangeと例外のどちらが発生するかはブラウザ依存
    // 両方発生するケースもある
    console.log(e);
    callback(e);
  }
}
