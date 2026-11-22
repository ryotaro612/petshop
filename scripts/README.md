# Local processing scripts

ローカルCPUで動く後処理ツールです。RunPodにも生成モデルにも接続せず、認証情報も読みません。GPU推論の外側、つまり入力の検証、マスク合成、動画からのフレーム抽出、ループ選定、780x780への整形、スプライトシート梱包だけを担当します。

## 実行

`uv` で依存を解決します。ローカルにPillow/ffmpegを入れる必要はありません (ffmpegバイナリは `imageio-ffmpeg` が同梱します)。

```sh
uv run --project scripts petshop --help
```

`scripts/` 内から実行する場合は `uv run petshop --help` です。各コマンドは結果をJSONで標準出力に書くので、そのまま記録や次工程の入力に使えます。

## パイプライン

```text
inspect -> composite -> extract-frames -> select-loop -> preview-loop
        -> normalize -> pack-atlas
```

### inspect

画像1枚、またはフレームディレクトリのサイズ/モード/アルファを報告します。サイズが揃っているかを `uniform` で確認できます。

```sh
uv run --project scripts petshop inspect path/to/frames
```

### composite — マスク外の画素を保持する

部分編集の要件を保証する工程です。モデルがキャンバス全体を描き直して返しても、最終出力でマスク外は元画像のままになります。元画像のアルファも復元するので、切り抜きが潰れません。

```sh
uv run --project scripts petshop composite \
  --original original.png --edited model_output.png --mask mask.png \
  --output composited.png --feather 2
```

マスクは白が編集対象です。逆の場合は `--invert-mask`。`--feather` は境界にガウスぼかしをかけて馴染ませますが、ぼかした分だけマスク外にわずかに影響します。完全な一致が必要なときは `--feather 0` (既定) を使ってください。`--edited` のサイズが元画像と違う場合は元画像サイズへ合わせ、その旨をJSONの `edited_resized_to_original` で報告します。

### extract-frames

生成された動画をPNG連番に展開します。`--count` で等間隔サンプリングできます。

```sh
uv run --project scripts petshop extract-frames \
  --video motion.mp4 --output-dir frames --count 120
```

### select-loop / preview-loop

ループ区間の候補を出し、目で確認します。採点は各フレームをグレースケールに縮小し、巻き戻し境界 (区間の最終フレームと先頭フレーム) の平均絶対差を測るだけの単純なものです。候補を並べるためのもので、最終判断は `preview-loop` の見た目で行ってください。

```sh
uv run --project scripts petshop select-loop frames --length 56 --top 5 --report loop.json
uv run --project scripts petshop preview-loop frames --output loop.webp --start 3 --length 56 --fps 24
```

`seam_distance` は小さいほど継ぎ目が滑らかです。ただし `mean_motion` がほぼ0の区間は「ほとんど動いていないから継ぎ目も小さい」だけなので、必ずプレビューを見てください。

### normalize

選んだ区間を既定780x780の正方セルに揃えます。`--start` / `--length` に `select-loop` の結果を渡します。

```sh
uv run --project scripts petshop normalize frames \
  --output-dir cells --start 3 --length 56 --mode pad --background transparent
```

`--mode pad` はアスペクト比を保って余白を足す (既定)、`cover` は中央切り抜き、`stretch` は引き伸ばしです。

### pack-atlas

セルをシートに梱包し、同名の `.json` に再現用メタデータを書き出します。

```sh
uv run --project scripts petshop pack-atlas cells \
  --output sheet.png --meta prompt="..." --meta seed=1234 --meta workflow=wan_i2v_v3
```

既定は56フレーム・780pxセル・8列×7行 (6240x5460)。`--columns` で変更できます。セルが780pxに揃っていない場合はエラーになるので、先に `normalize` を実行するか `--normalize` を付けてください。`--meta key=value` と `--meta-json file.json` で記録したprompt/seed/workflow情報はシートのJSONに残ります。

## 設計上の注意

- 56フレーム・780pxは既定値であって、動画生成がそのまま出す前提ではありません。抽出と整形はここで行います。
- ループ採点は補助です。表情やプロップの切り替わりのように意味的な連続性が要る動きは、スコアだけでは判断できません。
- 生成物 (PNG/動画/シート) はcommit対象外です。
