# ■ SS Maniacs サイト用 JSON/JS 作成 ■

## シーンリスト、オブジェクトファインダ用シーン情報JSON

1. シーン・オブジェクト情報の読み込み、変換

    $ ReadSceneResource.py resdir [id ...]
        -> ./scene_{id}_data.json


2. 多言語用JSON を生成（シーン名、オブジェクト名）

	$ MakeLangJson.py resdir datadir outdir
		=> {outdir}/scene_info.{lang}.json


3. シーン・オブジェクト画像の変換

	$ MakeConvertList.py resdir imgdir scene_{id}_data.json [...] > convlist.txt
	$ convert_images.sh convlist.tsv

    (縮小版イメージの作成)
	$ shrink_images.sh imgdir lo-imgdir


4. シーン情報JSON を生成 (SceneParams.htmlから参照）

	$ MakeSceneJson.py resdir imgdir outdir prm [embed]
		=> {outdir}/scene_{id}_prm.json

	embed 未指定の場合、JSON内にはイメージパスのみ格納
	embed を指定した場合 data: スキームによるイメージ埋め込み

5. オブジェクトファインダJSONを生成 (ObjectFinder.htmlから参照）

	$ MakeSceneJson.py resdir imgdir {outdir} bg obj
		=> {outdir}/scene_{id}_bgp.json
		=> {outdir}/scene_{id}_objp.json

	embed 未指定でイメージパスのみ格納

6. オブジェクトファインダをパスモードで実行

	http://.../ObjectFinder.html?image_root=relpath&bg_control=true

7. scene_template.jsonを適宜修正 ("type":"skip", "type":"effect" の追記など)

8. オブジェクトファインダJSONイメージ埋め込み版を生成

	$ MakeSceneJson.py resdir imgdir {outdir} bg obj embed
		=> {outdir}/scene_{id}_bg.json
		=> {outdir}/scene_{id}_obj.json

	scene_template.jsonを修正していない場合は EmbedImageData.py で
	_bgp.json および _objp.json から変換しても良い

	$ EmbedImageData.py imgdir < scene_{id}_bgp.json > scene_{id}_bg.json
	$ EmbedImageData.py imgdir < scene_{id}_objp.json > scene_{id}_obj.json

	$ EmbedImageData.py imgdir-low < scene_{id}_bgp.json > scene_{id}_bgl.json
	$ EmbedImageData.py imgdir-low < scene_{id}_objp.json > scene_{id}_objl.json

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
