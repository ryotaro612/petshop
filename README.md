# Petshop

ローカルのComfyUIを制作UI・ワークフロー編集環境として使い、画像編集と動画生成のGPU推論をRunPod Serverlessで実行し、動画をフレーム画像とスプライトシートへ変換するためのプロジェクトです。

## 目標

- 入力イラスト全体をプロンプトで編集する。
- マスクで指定した範囲だけを微修正する。範囲外の画素は元画像から再合成して保持する。
- 気に入った画像から短い動画を生成する。静止画・プロンプト・任意の開始/終了ポーズを入力にできる構成を目指す。
- 動画からフレームを抽出し、ループを確認・調整して、各フレーム780x780のスプライトシートを出力する。56フレームを既定値とする。
- 生成モデルはローカルMacに常駐させず、RunPod Serverless GPU workerで動かす。ComfyUIの管理画面と軽量な前後処理はローカルで行う。
- RunPodのEndpoint/Templateなどのインフラ設定はTerraformで再現可能にする。
- プロンプトやseed等の設定を残し、結果を見比べて反復しやすくする。

## 構成

```text
Mac
  ComfyUI (venv直起動。UI / mask paint / workflow authoring)
    -> local RunPod client/custom node (API keyはサーバー側環境変数)
    -> RunPod Serverless endpoint (GPU inference)
  Local post-processing: mask composite, video frame extraction, loop preview,
                         resize/pad to 780x780, atlas packing

Terraform
  -> RunPod Serverless endpoint and worker configuration
```

UIはまずComfyUIを使って編集ワークフローを検証します。ワークフローが定まった後に専用UIが必要なら、画像キャンバス、マスク、prompt、結果比較、動画/シートプレビューに絞った画面を追加します。RunPodに置くのはGPU推論workerで、制作UIではありません。

## 編集の扱い

- 全体編集: 元画像と指示をworkerに送る。
- 部分編集: 元画像、白黒mask、指示を送る。worker側でinpaintを行い、出力をマスクで元画像に合成する。モデルがマスク領域以外を書き換える場合でも、最終合成で範囲外を保持する。
- 画像やmaskをAPI入力に含める形式、最大サイズ、workerへの受け渡し方法は選ぶモデル/RunPod workflowに合わせて実装する。
- 最初/最後のポーズを正確に指定する機能や服飾品の着脱は、単純なテキスト指示のみで保証できない。参照画像、pose/control条件、ループ用の始終フレーム調整を別途検証する。

## ディレクトリ

- `terraform/`: RunPod Serverless infrastructure as code
- `comfyui/workflows/`: ComfyUI workflow JSONを保存
- `scripts/`: フレーム抽出、整形、シート梱包などのローカルツール

## セットアップ状況

この初期骨格では、Terraform endpointの定義と手順、ローカル後処理CLI (`scripts/`) を用意します。モデル/workerイメージ、GPU pool、APIリクエスト形式は未選定のため、placeholderのままです。RunPodへ課金リソースを作る `terraform apply` は実行しません。

未実装なのは、推論worker本体に関わる部分です。worker Dockerイメージとモデルの選定、RunPod APIのリクエスト/レスポンス形式、ComfyUIからRunPodを呼ぶcustom node/client、画像・maskのアップロード方式が残っています。ローカル後処理 (マスク合成、フレーム抽出、ループ選定、780x780整形、シート梱包) は動作します。

### 前提

- Terraform >= 1.6
- uv (ComfyUIとローカル後処理スクリプト用。Python環境とffmpegはuvが解決します)
- RunPod API key
- RunPod向けのServerless worker Docker image (ComfyUI worker等)
- ComfyUI (Mac上に `./comfyui/setup.sh` でインストール。ローカルでGPU推論はしない)

### Terraform

```sh
cd terraform
cp terraform.tfvars.example terraform.tfvars
# terraform.tfvarsにworker_image、GPU pool等を設定
export RUNPOD_API_KEY='...'
terraform init
terraform validate
terraform plan
# 内容と料金設定を確認してから明示的に適用
terraform apply
```

RunPod API keyをGitにcommitしないでください。`terraform.tfvars` とstateも秘密情報を含み得るため管理対象外です。Serverlessのmin workersは既定で0です。モデル重みのキャッシュ先やworker imageを設定しないままendpointをapplyしても、推論workerは完成しません。

### ComfyUI

ComfyUIはDockerを使わず、comfy-cliでリポジトリ内にインストールして起動します。**リポジトリ外にはファイルを置きません。**

```sh
make setup   # 依存関係とComfyUIをリポジトリ内に用意
make launch  # comfy-cli で ComfyUI を起動 (http://127.0.0.1:8188、Ctrl-C で停止)
make        # ターゲット一覧
```

前提は `git`、`uv`、Python 3.14 (Homebrewの `python@3.14` など) がインストール済みであることです。uvのパッケージキャッシュは `.cache/uv` に置き、Pythonはダウンロードせず既存のものを使います。ComfyUI本体はcomfy-cliが取得します (`comfy-cli install --skip-requirement --skip-torch-or-directml --skip-manager`)。依存関係は `comfyui/uv.lock` からuvが入れます。

構成は次のとおりです。

| パス | 内容 | git |
|---|---|---|
| `comfyui/pyproject.toml` | comfy-cliとComfyUIの依存を宣言 | 追跡 |
| `comfyui/ComfyUI/` | upstreamのclone (comfy-cliが管理) | 無視 |
| `comfyui/.venv/` | Python依存 | 無視 |

ワークスペースは `comfy-cli set-default <repo>/comfyui/ComfyUI` で固定済みです。これをしないとcomfy-cliは既定の `~/Documents/comfy/ComfyUI` を見に行きます。

**ComfyUIの依存は `uv add -r ComfyUI/requirements.txt` で `pyproject.toml` に宣言してあります。** `uv sync` は宣言されていないパッケージを削除するため、`uv pip install` で入れただけだとtorch等が消えます。ComfyUI本体を更新したとき (`git -C comfyui/ComfyUI pull`) は `uv add -r ComfyUI/requirements.txt` を再実行してください。

M3 MaxではMPSが使われます (`Device: mps`)。ローカルGPU推論を避ける場合は `comfyui/.venv/bin/comfy-cli launch -- --cpu` のようにComfyUIへ `--cpu` を渡してください。

RunPod API呼び出し用custom node/clientと画像アップロード形式は未実装です。Docker構成は廃止しましたが `git show aed7b64:comfyui/compose.yaml` で復元できます。

### ローカル後処理 (`scripts/`)

RunPodとモデル選定に依存しない後処理は実装済みです。`uv` で実行し、ローカルにPillowやffmpegを入れる必要はありません。

```sh
uv run --project scripts petshop --help
```

```text
inspect -> composite -> extract-frames -> select-loop -> preview-loop
        -> normalize -> pack-atlas
```

- `composite`: 部分編集の結果をマスクで元画像に合成する。マスク外の画素と元のアルファを保持するので、モデルがキャンバス全体を描き直しても範囲外は変わらない。
- `extract-frames`: 生成動画をPNG連番へ展開する。
- `select-loop` / `preview-loop`: 巻き戻し境界の差分でループ候補を並べ、WebP/GIFで実際の見た目を確認する。
- `normalize`: 選んだ区間を780x780のセルへ整形する (pad / cover / stretch)。
- `pack-atlas`: 56セルを8x7 (6240x5460) のシートへ梱包し、prompt/seed/workflowを含むJSONを併記する。

各コマンドの詳細は `scripts/README.md` を参照してください。

### スプライトシート

目標は2〜3秒程度の短い動画から56フレームを作り、各セルを780x780に揃えることです。動画FPSと抽出間隔をもとにフレームを選び、ループ境界をプレビューして、画像をパディング/リサイズしてからシート化します。動画生成結果が56枚・780pxのシートとして直接出る前提にはしません。この工程は上記 `scripts/` のコマンド群で実行できます。入力となる動画・編集結果を作る部分 (RunPod worker) が未実装です。

## 開発上のルール

- `AGENTS.md` と `CLAUDE.md` を参照。
- 秘密鍵、RunPod API key、個人画像、生成物、Terraform stateはcommitしない。
- インフラ変更時は `terraform plan` を確認し、意図しない破棄や高いworker設定を避ける。
