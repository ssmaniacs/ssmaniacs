window.onerror = function (message, url, line) {
  if (line <= 1) {  // ブラウザ起源の例外
    return false;   // スクリプト実行継続
  }
  else {
    alert(message + '\n' + url + ':' + line);
    return true;  // スクリプト実行終了
  }
}
var BG_WIDTH = 1480;          // バックグラウンドイメージの論理幅
var BG_HEIGHT = 690;          // バックグラウンドイメージの論理高さ

var scale = 2;                // 表示倍率（1/scale で表示）

var scene_canvas;             // シーン描画キャンバス
var scene_context;            // シーン描画コンテキスト

var menu_canvas;              // メニュー描画キャンバス
var menu_context;             // メニュー描画コンテキスト

var scene_info = null;        // シーンイメージ情報
var object_info = null;       // オブジェクトイメージ情報
var object_images = null;     // オブジェクトイメージリスト
var current_menu = null;      // メニュー情報
var current_morph = null;     // 現在のモーフ形態
var morph_timer = null;       // モーフ更新タイマー

var show_bg_control = false;  // 背景描画コントロールの表示
var image_root = null;        // イメージをパスからロードする際のルート
var image_scale = 1;          // ローレゾ時のイメージ倍率
var local_mode = false;       // ローカルモード(JSONを動的ロードしない)

// 初期化
function init(initial_scene) {
  // デバッグモードなど
  if (location.search || location.hash) {
    var options;
    if (location.search) {
      options = location.search.substr(1).split('&');
    }
    else {
      options = location.hash.substr(1).split('&');
    }

    options.forEach(function(s) {
      var p = s.split('=');
      if (p[0] == 'help') {
        alert('bg_control=true\nimage_root=<image root>\nimage_scale={1|2}\n');
      }
      else if (p[0] == 'bg_control') {
        document.getElementById('background_control').style.display = 'block';
      }
      else if (p[0] == 'image_root') {
        if (!local_mode) {
          image_root = p[1].toLowerCase();
        }
      }
      else if (p[0] == 'image_scale') {
        if (p[1] == 1 || p[1] == 2) {
          if (!local_mode) {
            image_scale = p[1];
            document.getElementById('lowres').checked = (image_scale == 2);
          }
        }
        else {
          alert('image_scale must be 1 or 2\n');
        }
      }
    });
  }

  // シーン描画キャンバス、コンテキストを初期化
  scene_canvas = document.getElementById('scene_canvas');
  scene_canvas.width = BG_WIDTH / scale;
  scene_canvas.height = BG_HEIGHT / scale;

  scene_context = scene_canvas.getContext('2d');
  scene_context.scale(1 / scale * image_scale, 1 / scale * image_scale);

  // ローディングスピナーサイズを調整
  var spframe = document.getElementById('scene_spframe');
  spframe.style.width = (BG_WIDTH / scale) + 'px';
  spframe.style.height = (BG_HEIGHT / scale) + 'px';

  // ブラウザによってキャンバスの下に数ピクセルの余白ができる。
  // 見た目を合わせるためスピナーの下にも同じだけの余白を入れる。
  var cvframe = document.getElementById('scene_cvframe');
  if (cvframe.offsetHeight > spframe.offsetHeight) {
    var diff = cvframe.offsetHeight - spframe.offsetHeight;
    var spacer = document.getElementById('scene_spacer');
    spacer.style.height = diff + 'px';
  }

  // メニュー描画キャンバスを初期化
  menu_canvas = document.getElementById('menu_canvas');
  menu_context = menu_canvas.getContext('2d');

  // シーン選択リストに項目を設定
  var selector = document.getElementById('select_scene');

  for (var scene in scene_list) {
    var option = document.createElement('option');
    option.setAttribute('value', scene);
    option.innerHTML = scene_list[scene];
    selector.appendChild(option);
  }

  // 初期シーンを設定
  selector.value = initial_scene;
  selector.disabled = false;

  scene_change();
}


function show_spinners() {

  // シーンキャンバス非表示、スピナー表示
  document.getElementById('scene_cvframe').style.display = 'none';
  document.getElementById('scene_spframe').style.display = 'table-cell';
  document.getElementById('scene_spinner').style.display = 'block';
  document.getElementById('scene_spacer').style.display = 'block';

  // メニューキャンバス非表示、スピナー表示（スピナー幅をメニューと同じにする）
  var cvframe = document.getElementById('menu_cvframe');
  var spframe = document.getElementById('menu_spframe');

  var menuwidth = cvframe.offsetWidth;
  if (menuwidth == 0) {
    menuwidth = BG_WIDTH / scale;
  }
  spframe.style.width = menuwidth + 'px';
  cvframe.style.display = 'none';
  spframe.style.display = 'table-cell';
  document.getElementById('menu_spinner').style.display = 'block';
  document.getElementById('menu_errtext').innerHTML = '';
}

//  シーンの変更
function scene_change() {
  show_spinners();

  // コントロール類の無効化
  ['scale', 'effect', 'mode_sel', 'drawobj', 'topmost', 'encircle',
  'morph0', 'morph1', 'morph2'].forEach(function(id) {
    document.getElementById(id).disabled = true;
  });

  ['effect_label', 'drawobj_label', 'topmost_label', 'encircle_label',
  'morph0_label', 'morph1_label', 'morph2_label'].forEach(function(id) {
    document.getElementById(id).style.color = 'silver';
  });

  if (local_mode) {
    load_scene_images();
    load_object_images();
    return;
  }

  // 描画オブジェクトセレクタの初期化
  var objlist = document.getElementById('select_object')

  while (objlist.firstChild) {
    objlist.removeChild(objlist.firstChild);
  }

  // 前シーンのデータをクリア
  scene_info = null;
  object_info = null;
  object_images = null;
  current_menu = null;

  // シーンデータJSONロード
  var scene = document.getElementById('select_scene').value;

  document.getElementById('scene_sptext').innerHTML = 'ロード中...';

  var bgfile;
  var objfile;
  if (image_root) {
    // テスト用: 個々のイメージをパスからロード
    bgfile = './scene_' + scene + '_bgp.json'
    objfile = './scene_' + scene + '_objp.json'
  }
  else if (image_scale == 2) {
    // ローレゾ版イメージデータ埋め込み
    bgfile = './scene_' + scene + '_bgl.json'
    objfile = './scene_' + scene + '_objl.json'
  }
  else {
    // 通常（フルレゾ）版イメージデータ埋め込み
    bgfile = './scene_' + scene + '_bg.json'
    objfile = './scene_' + scene + '_obj.json'
  }

  console.log('Loading ' + bgfile + ' and ' + objfile);

  // IEでJSONロード中に画面が更新されない（スピナーが表示されない）ので、
  // 遅延実行（スピナーを表示させてからロード開始）
  setTimeout(function(){
    loadJSON(bgfile, load_scene_done);
  }, 100);

  setTimeout(function(){
    loadJSON(objfile, load_object_done);
  }, 200);
}

function scene_load_error(message) {

  // JSONデータ取得エラー
  document.getElementById('scene_spinner').style.display = 'none';

  var ua = navigator.userAgent.toLowerCase();
  var proto = location.protocol;

  // Chromeでローカルファイルの場合、エラーにならず空データが返る
  if (ua.indexOf('chrome') > -1 && proto == 'file:' && !message) {
    message = 'Chromeでローカルファイルにアクセスするには<br>' +
      '以下のオプションをつけてChromeを起動してください<br>' +
      '（詳しくは自分でググって）' +
      '<pre>--allow-file-access-from-files</pre>';
  }

  document.getElementById('scene_sptext').innerHTML =
    'イメージデータロードエラー' + (message ? ('<p>' + message): '');
}

// バックグラウンド情報ロード確認
function load_scene_done(resp) {

  if (!resp || resp instanceof Error) {
    scene_load_error(resp ? resp.message : '');
  }
  else {
    scene_info = JSON.parse(resp);
    load_scene_images();
  }
}

// バックグラウンドイメージをロード
function load_scene_images() {
  // エフェクトを描画するかどうか
  var doeffect = document.getElementById('effect').checked;
  var haseffect = false;

  // オブジェクトごとに描画セレクタを生成、イメージをロード
  var totalimages = scene_info.length;
  var loadedimages = 0;

  var objlist = document.getElementById('select_object')

  var load_failed = false;

  for (var idx in scene_info) {
    if (load_failed) {
      return;
    }

    var img = scene_info[idx];

    if (img.type == 'skip') {
      loadedimages++;
      continue;
    }

    var iseffect = (img.type == 'effect');

    var check = document.createElement('input');
    check.type = 'checkbox';
    check.id = 'cb' + idx;
    check.iseffect = iseffect;
    objlist.appendChild(check);

    var label = document.createElement('label');
    label.htmlFor = 'cb' + idx;
    label.innerHTML = img.path.split('/').pop().split('.')[0];
    objlist.appendChild(label);

    if (iseffect) {
      haseffect = true;
    }

    // エフェクト未チェックの場合、effectアイテムはチェックをオフにしておく
    check.checked = (!iseffect || doeffect);

    if (img.image) {
      loadedimages++;
    }
    else {
      img.image = new Image();
      img.image.onload = function(){
        loadedimages++;

        if (loadedimages == totalimages){
          drawscene();
        }
      }
      img.image.onerror = function(){
        load_failed = true;
        scene_load_error('画像読み込みエラー');
      }

      if ('data' in img) {
        img.image.src = img.data;
      }
      else {
        img.image.src = image_root + '/' + img.path;
      }
    }
  }

  document.getElementById('scale').disabled = false;

  if (haseffect) {
    document.getElementById('effect').disabled = false;
    document.getElementById('effect_label').style.color = 'black';
  }

  drawscene();
}

function object_load_error(message) {
  document.getElementById('menu_spinner').style.display = 'none';
  document.getElementById('menu_errtext').innerHTML =
    'イメージデータロードエラー' + (message ? ('<p>' + message) : '');
}

// 探索オブジェクト情報ロード確認
function load_object_done(resp) {
  if (!resp || resp instanceof Error) {
    object_load_error((resp && resp.message) ? ('<p>' + resp.message) : '');
  }
  else {
    object_info = JSON.parse(resp);
    load_object_images();
  }
}

// 探索オブジェクトイメージのロード
function load_object_images() {
  object_images = [];

  function load_objimg(pic) {
    if (!('ref' in pic && pic.ref in object_images)) {
      var idx = object_images.length;

      object_images[idx] = new Image();
      if ('data' in pic) {
        object_images[idx].url = pic.data;
      }
      else if ('url' in pic) {
        object_images[idx].url = pic.url;
      }
      else if ('path' in pic) {
        object_images[idx].url = image_root + '/' + pic.path;
      }

      pic.ref = idx;
    }
  }

  var obj0 = object_info;

  for (var idx0 in obj0.form) {
    var obj1 = obj0.form[idx0];
    load_objimg(obj1);            // シルエットイメージ

    for (var idx1 in obj1.images) {
      var obj2 = obj1.images[idx1];

      for (var idx2 in obj2) {
        load_objimg(obj2[idx2]);  // クリックイメージ
      }
    }
  }

  for (var idx0 in obj0.part) {
    var obj1 = obj0.part[idx0];
    load_objimg(obj1);        // 組み合わせイメージ

    for (var idx1 in obj1.pieces) {
      var obj2 = obj1.pieces[idx1];
      load_objimg(obj2);      // 部品イメージ（メニュー）

      for (var idx2 in obj2.images) {
        var obj3 = obj2.images[idx2];

        for (var idx3 in obj3) {
          load_objimg(obj3[idx3]);  // 部品イメージ（クリック）
        }
      }
    }
  }

  for (var idx0 in obj0.morph) {
    var obj1 = obj0.morph[idx0];

    for (var idx1 in obj1.images) {
      var obj2 = obj1.images[idx1];

      for (var idx2 in obj2) {
        load_objimg(obj2[idx2]);
      }
    }
  }

  var totalobjects = object_images.length;
  var loadedobjects = 0;
  var load_failed = false

  for (var idx in object_images) {
    if (load_failed) {
      return;
    }

    if (object_images[idx].url) {
      object_images[idx].onload = function(){
        loadedobjects++;

        if (loadedobjects == totalobjects){
          mode_change();
        }
      }
/*
      object_images[idx].onerror = function(){
        load_failed = true;
        object_load_error('画像読み込みエラー');
      }
*/
      object_images[idx].src = object_images[idx].url;
      delete object_images[idx].url;
    }
  }

  mode_change();
}

//  イメージを描画する
function drawscene() {
  // 現在のシーンのイメージが全てロード済みか
  for (var idx in scene_info) {
    var img = scene_info[idx];

    if (img.type != 'skip' && !(img.image.src && img.image.complete)) {
      return;
    }
  }

  if (morph_timer) {
    clearTimeout(morph_timer);
    morph_timer = null;
  }

  var drawobj = document.getElementById('drawobj').checked;
  var encircle = document.getElementById('encircle').checked;
  var topmost = document.getElementById('topmost').checked;

  // キャンバスクリア
  scene_context.clearRect(0, 0, BG_WIDTH / image_scale, BG_HEIGHT / image_scale);

  // バックグラウンドを描画
  // - オブジェクト最前面指定がある場合、描画指定されているもの全て描画
  // - オブジェクト最前面指定がない場合、effectイメージはオブジェクトの後で描画
  for (var idx in scene_info) {
    var img = scene_info[idx];

    if (img.type == 'skip' || (img.type == 'effect' && !topmost)) {
      continue;
    }

    if (document.getElementById('cb' + idx).checked) {
      scene_context.drawImage(img.image, img.x / image_scale, img.y / image_scale);
    }
  }

  // オブジェクトを描画
  if (current_menu && current_menu.select != null) {
    var imglist = current_menu.items[current_menu.select].obj.images;

    // 描画対象イメージタグを決定
    var drawtarget;

    if (document.getElementById('mode_sel').value == 'morph') {
      if (document.getElementById('morph0').checked) {
        if (current_morph == -1) {
          current_morph = -2;
          drawtarget = 'pic2';
        }
        else {
          current_morph = -1;
          drawtarget = 'pic1';
        }
      }
      else if (document.getElementById('morph1').checked) {
        current_morph = 1;
        drawtarget = 'pic1';
      }
      else if (document.getElementById('morph2').checked) {
        current_morph = 2;
        drawtarget = 'pic2';
      }
    }
    else {
      current_morph = 0;
      drawtarget = 'pic';
    }

    // オブジェクト、カバーを描画
    if (drawobj) {
      for (var idx in imglist) {
        var obj = imglist[idx]
        var pic = obj[drawtarget];
        scene_context.drawImage(object_images[pic.ref], pic.x / image_scale, pic.y / image_scale);

        pic = obj['cover']
        if (!topmost && pic) {
          scene_context.drawImage(object_images[pic.ref], pic.x / image_scale, pic.y / image_scale);
        }
      }
    }
  }
  else {
    current_morph = 0;
  }


  // オブジェクト最前面指定がない場合、effectイメージを描画
  if (!topmost) {
    for (var idx in scene_info) {
      var img = scene_info[idx];

      if (img.type == 'effect' && document.getElementById('cb' + idx).checked) {
        scene_context.drawImage(img.image, img.x / image_scale, img.y / image_scale);
      }
    }
  }

  // オブジェクトの囲みを描画
  if (imglist && encircle) {
    scene_context.lineWidth = 4 / image_scale;
    scene_context.strokeStyle = '#ff0000';

    for (var idx in imglist) {
      var obj = imglist[idx]
      for (var idx1 in obj) {
        if (idx1 == drawtarget) {
          var pic = obj[idx1];
          var x = pic.x + (pic.w / 2);
          var y = pic.y + (pic.h / 2);
          var r = (pic.w + pic.h) / 2 * 1;
          if (r > 100) {
            r = 100;
          }
          scene_context.beginPath();
          scene_context.arc(x / image_scale, y / image_scale, r / image_scale, 0, 2 * Math.PI, false);
          scene_context.stroke();
          break;
        }
      }
    }
  }

  if (current_morph < 0) {
    morph_timer = setTimeout(function(){
      morph_timer = null;
      drawscene();
    }, 3000);
  }


  // スピナーを非表示、キャンバスを表示
  document.getElementById('scene_cvframe').style.display = 'block';
  document.getElementById('scene_spframe').style.display = 'none';
  document.getElementById('scene_spacer').style.display = 'none';
}


function change_res() {
  image_scale = (document.getElementById('lowres').checked ? 2 : 1);
  var scale = 10 / document.getElementById('scale').value;
  scene_canvas.width = BG_WIDTH / scale;
  scene_canvas.height = BG_HEIGHT / scale;
  scene_context.scale(1 / scale * image_scale, 1 / scale * image_scale);
  scene_change();
}


function drawobject() {
  if (current_menu && current_menu.select != null) {
    drawscene();
  }
}


//  スライダー・ボタンによるキャンバスのスケーリング
function scalechange() {
  var scale = 10 / document.getElementById('scale').value;

  scene_canvas.width = BG_WIDTH / scale;
  scene_canvas.height = BG_HEIGHT / scale;
  scene_context.scale(1 / scale * image_scale, 1 / scale * image_scale);

  var sf = document.getElementById('scene_spframe');
  sf.style.width = (BG_WIDTH / scale) + 'px';
  sf.style.height = (BG_HEIGHT / scale) + 'px';

  drawscene();
}


// 拡大率ダウン
function scale_down() {
  document.getElementById('scale').value--;
  scalechange();
}


// 拡大率アップ
function scale_up() {
  document.getElementById('scale').value++;
  scalechange();
}


// 背景色変更
function color_change() {
  document.getElementById('scene_canvas').style.backgroundColor = document.getElementById('background').value;
}


// 全オブジェクト描画ボタン
function all_objects(val) {
  var children = document.getElementById('select_object').children;
  var doeffect = document.getElementById('effect').checked;

  for (var idx = 0; idx < children.length; idx++) {
    if (children[idx].type == 'checkbox') {
      if (val == -1) {
        children[idx].checked = (!children[idx].iseffect || doeffect);
      }
      else {
        children[idx].checked = (val != 0);
      }
    }
  }

  drawscene();
}


// モード変更：オブジェクトメニュー情報を更新
function mode_change() {
  // 以前のメニューがあったら破棄する
  if (current_menu) {
    if (current_menu.select != null) {
      // 選択中(=表示中)のアイテムがあれば画面を再描画
      current_menu.select = null;
      drawscene();
    }
    delete current_menu;
    current_menu = null;
  }

  ['mode_sel', 'drawobj', 'topmost', 'encircle'].forEach(function(id) {
    document.getElementById(id).disabled = false;
  });

  ['drawobj_label', 'topmost_label', 'encircle_label'].forEach(function(id) {
    document.getElementById(id).style.color = 'black';
  });

  var mode = document.getElementById('mode_sel').value;

  // モーフ形態選択ボタンの有効・無効切り替え
  for (var i = 0; i <= 2; i++) {
    document.getElementById('morph' + i).disabled = (mode != 'morph');
    document.getElementById('morph' + i + '_label').style.color = ((mode != 'morph') ? 'silver' : 'black');
  }

  // メニュー構造を準備
  current_menu = {
    'mode': mode,
    'select': null,
    'items': []
  };

  var obj1 = object_info[mode];

  if (mode == 'form') {
    current_menu.width = obj1.length;
    current_menu.height = 1;

    for (var idx1 in obj1) {
      var obj2 = obj1[idx1];
      current_menu.items.push({'obj': obj2, 'x': 128 * idx1, 'y': 0});
    }
  }
  else if (mode == 'part') {
    current_menu.width = 6;
    current_menu.height = obj1.length;

    for (var idx1 in obj1) {
      var obj2 = obj1[idx1];
      current_menu.items.push({'obj': obj2, 'x': 0, 'y': 128 * idx1, 'noselect': true});

      for (var idx2 in obj2.pieces) {
        var obj3 = obj2.pieces[idx2];
        current_menu.items.push({'obj': obj3, 'x': 128 * (1 + (+idx2)), 'y': 128 * idx1});
      }
    }
  }
  else if (mode == 'morph') {
    current_menu.width = obj1.length;
    current_menu.height = 1;

    for (var idx1 in obj1) {
      var obj2 = obj1[idx1];
      current_menu.items.push({'obj': obj2, 'x': 128 * idx1, 'y': 0});
    }
  }

  draw_menu();
}


// オブジェクトメニューを描画する
function draw_menu()
{
  if (!object_images) {
    return;
  }
  for (var idx in object_images) {
    if (!(object_images[idx].src && object_images[idx].complete)) {
      return;
    }
  }

  menu_canvas.width = current_menu.width * 128;
  menu_canvas.height = current_menu.height * 128;

  menu_context.clearRect(0, 0, menu_canvas.width, menu_canvas.height);
  menu_context.font = '14px sans-serif';
  menu_context.textAlign = 'center';
  menu_context.textBaseline = 'bottom';

  if (current_menu.mode == 'part') {
    menu_context.fillStyle = '#cccccc';
    menu_context.fillRect(0, 0, 128, menu_canvas.height);
  }

  for (var idx in current_menu.items) {
    draw_menuitem(current_menu.items[idx], false, (idx == current_menu.select));
  }

  document.getElementById('menu_cvframe').style.display = 'block';
  document.getElementById('menu_spframe').style.display = 'none';
}


MENUICON_MAX = 100; // 最大メニューアイコンサイズ
MENUICON_MIN = 80;  // 最小メニューアイコンサイズ

// メニュー項目を描画する
function draw_menuitem(menuitem, erasebg, selected)
{
  var obj = menuitem.obj;

  draw_menuframe(menuitem.x, menuitem.y, erasebg, selected);

  if (current_menu.mode == 'form') {
    var img = object_images[obj.ref];
    var size = adjust_imgsize(img.width, img.height, MENUICON_MAX, 0);

    var x = parseInt((128 - size[0]) / 2);
    var y = parseInt((112 - size[1]) / 2);

    menu_context.drawImage(img, menuitem.x + x, menuitem.y + y, size[0], size[1]);

    menu_context.fillStyle = 'black';
    menu_context.fillText(obj.name, menuitem.x + 64, menuitem.y + 120, 128);
  }
  else if (current_menu.mode == 'part') {
    var img = object_images[obj.ref];
    var size = adjust_imgsize(img.width, img.height, MENUICON_MAX, 0);
    var x = parseInt((128 - size[0]) / 2);
    var y = parseInt((128 - size[1]) / 2);

    menu_context.drawImage(img, menuitem.x + x, menuitem.y + y, size[0], size[1]);
  }
  else if (current_menu.mode == 'morph') {
    var obj1 = obj.images[0].pic1;
    var img1 = object_images[obj1.ref];
    var size1 = adjust_imgsize(img1.width, img1.height, MENUICON_MIN, MENUICON_MIN);
    var x1 = parseInt((128 - size1[0]) / 2 - 15);
    var y1 = parseInt((128 - size1[1]) / 2 - 15);

    var obj2 = obj.images[0].pic2;
    var img2 = object_images[obj2.ref];
    var size2 = adjust_imgsize(img2.width, img2.height, MENUICON_MIN, MENUICON_MIN);
    var x2 = parseInt((128 - size2[0]) / 2 + 15);
    var y2 = parseInt((128 - size2[1]) / 2 + 15);

    menu_context.drawImage(img1, menuitem.x + x1, menuitem.y + y1, size1[0], size1[1]);
    menu_context.drawImage(img2, menuitem.x + x2, menuitem.y + y2, size2[0], size2[1]);
  }
}


// メニュー項目の背景・選択枠を描画する
function draw_menuframe(x, y, erasebg, selected)
{
  if (erasebg) {
    menu_context.clearRect(x, y, 128, 128);
  }

  if (selected) {
    menu_context.lineWidth = 5;
    menu_context.strokeStyle = '#0489b1';
    menu_context.strokeRect(x + 5, y + 5, 128 - 10, 128 - 10);
  }
}


// 小さすぎ・大きすぎるアイコンイメージを拡大・縮小する
function adjust_imgsize(w, h, maxval, minval)
{
  //w *= image_scale;
  //h *= image_scale;
  maxval /= image_scale;
  minval /= image_scale;

  if (w > h) {
    if (w > maxval) {
      h = parseInt(h / (w / maxval));
      w = maxval;
    }
    else if (w < minval) {
      h = parseInt(h / (w / minval));
      w = minval;
    }
  }
  else {
    if (h > maxval) {
      w = parseInt(w / (h / maxval));
      h = maxval;
    }
    else if (h < minval) {
      w = parseInt(w / (h / minval));
      h = minval;
    }
  }

  return [w, h];
}


// メニュー領域クリック
function menu_click(e) {
  var x = e.offsetX;
  var y = e.offsetY;

  for (var idx in current_menu.items) {
    var menuitem = current_menu.items[idx];

    if (x > menuitem.x + 5 && x < menuitem.x + 123 && y > menuitem.y + 5 && y < menuitem.y + 123) {
      if (!menuitem.noselect) {
        if (current_menu.select != null) {
          // 選択中のアイテムを選択解除
          draw_menuitem(current_menu.items[current_menu.select], true, false);
        }

        if (current_menu.select == idx) {
          // 選択解除のみ
          current_menu.select = null;
        }
        else {
          // 新たなアイテムを選択
          current_menu.select = idx;
          draw_menuitem(menuitem, true, true);
        }

        // クリックしたアイテムをスクロール範囲内に
        var frame = e.currentTarget.parentNode;

        if (menuitem.x < frame.scrollLeft + 64) {
          var newleft = menuitem.x - 64;
          if (newleft < 0) {
            newleft = 0;
          }
          frame.scrollLeft = newleft;

        }
        else if (menuitem.x + 192 > frame.scrollLeft + frame.clientWidth) {
          var newleft = menuitem.x + 192 - frame.clientWidth;
          if (newleft + frame.clientWidth > frame.scrollWidth) {
            newleft = frame.scrollWidth - frame.clientWidth;
          }
          frame.scrollLeft = newleft;
        }

        if (menuitem.y < frame.scrollTop) {
          frame.scrollTop = menuitem.y;
        }
        else if (menuitem.y + 128 > frame.scrollTop + frame.clientHeight) {
          frame.scrollTop = menuitem.y + 128 - frame.clientHeight;
        }
      }

      drawscene();
      break;
    }
  }
}
