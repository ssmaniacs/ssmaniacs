# ■ SS Maniacs サイト用 JSON/JS 作成 ■

## シーンリスト、オブジェクトファインダ用シーン情報JSON

1. シーン・オブジェクト画像の変換

	$ MakeSceneJson.py resdir imgdir lang conv > convlist.txt
	$ convert_images.sh convlist.tsv

2. 縮小版イメージの作成

	$ shrink_images.sh imgdir lo-imgdir

3. シーンリスト JS を生成

	$ MakeSceneJson.py resdir imgdir lang list
		=> ./scene_idx.js

4. シーン情報JSON を生成 (SceneParams.htmlから参照）

	$ MakeSceneJson.py resdir imgdir lang prm [embed]
		=> ./scene_<n>_prm.json

	embed 未指定の場合、JSON内にはイメージパスのみ格納
	embed を指定した場合 data: スキームによるイメージ埋め込み

5. オブジェクトファインダJSONを生成 (ObjectFinder.htmlから参照）

	$ MakeSceneJson.py resdir imgdir lang bg obj
		=> ./scene_<n>_bgp.json
		=> ./scene_<n>_objp.json

	embed 未指定でイメージパスのみ格納

6. オブジェクトファインダをパスモードで実行

	http://.../ObjectFinder.html?image_root=relpath&bg_control=true

7. scene_template.jsonを適宜修正 ("type":"skip", "type":"effect" の追記など)

8. オブジェクトファインダJSONイメージ埋め込み版を生成

	$ MakeSceneJson.py resdir imgdir lang bg obj embed
		=> ./scene_<n>_bg.json
		=> ./scene_<n>_obj.json

	scene_template.jsonを修正していない場合は EmbedImageData.py で
	_bgp.json および _objp.json から変換しても良い

	$ EmbedImageData.py imgdir < scene_<n>_bgp.json > scene_<n>_bg.json
	$ EmbedImageData.py imgdir < scene_<n>_objp.json > scene_<n>_obj.json

	$ EmbedImageData.py imgdir-low < scene_<n>_bgp.json > scene_<n>_bgl.json
	$ EmbedImageData.py imgdir-low < scene_<n>_objp.json > scene_<n>_objl.json

	for i in *p.json; do echo $i; (python EmbedImageData.py ../../images < $i > ${i%p.json}.json) ; done
	for i in *p.json; do echo $i; (python EmbedImageData.py ../../images.lo < $i > ${i%p.json}l.json) ; done


## コレクションリスト用JSON

1. アイテム画像の変換

	$ collection_image.sh resdir imgdir | convert_images.sh [force]

2. JSON生成

	$ MakeCollectionList.py resdir dstdir lang {imgdir|-}

	imgdir未指定の場合、JSON内にはイメージパスのみ格納
	imgdirを指定した場合 data: スキームによるイメージ埋め込み

	dstdir に以下のファイルを生成(CollectionList.htmlから参照)：
		collections_idx.js
		collections_all.json
		collections_<n>.json
		artifacts_<n>.json
