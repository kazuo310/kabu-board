# 個別株診断ボード｜株価自動記録システム

半導体3社（東京エレクトロン 8035／アドバンテスト 6857／ルネサス 6723）の株価を
**毎日自動で記録し、①様子見／②撤退ラインを重ねたグラフを作る**仕組みです。
GitHub の無料機能（Actions＝定期実行／Pages＝公開）だけで、パソコンを開かなくても毎日更新されます。

## できること
- 平日の夕方に自動で株価を取得し、`data/` に日々ためていく
- `docs/compare.png`（3社の値動き比較・note貼付用）を毎日更新
- `docs/8035.png` などの銘柄別グラフ（①②ライン入り・note貼付用）を毎日更新
- `docs/index.html`（動かせるダッシュボード・GitHub Pagesで公開）を毎日更新

## noteへの出し方（ここが大事）
noteは「動く外部グラフ」をそのまま埋め込めません（対応サービスのみ）。なので運用はこの2本立てです。
- **画像を貼る**：診断編を書くとき、その時点の `compare.png` や銘柄別PNGを画像として記事に挿入する。
- **リンクで飛ばす**：記事に「最新のチャートはこちら」と GitHub Pages の公開URLを貼る。常に最新が見られます。

---

## セットアップ手順（初回だけ・順番どおりに）

### 1. GitHubアカウントを作る
https://github.com/ で無料登録（すでにあれば飛ばす）。

### 2. リポジトリ（置き場）を作る
- 右上の「＋」→「New repository」。
- Repository name は例：`kabu-board`。
- **Public**を選ぶ（無料でActions・Pagesが使えるため。中身は株価とグラフだけなので公開して問題ありません）。
- 「Create repository」。

### 3. ファイル一式をアップロードする
- 作ったリポジトリの画面で「Add file」→「Upload files」。
- このフォルダの中身（`.github` `config` `scripts` `docs` `data` `requirements.txt` `README.md`）を
  フォルダごとドラッグ＆ドロップ。
- 下の「Commit changes」を押す。

### 4. 初回だけ手動で動かす（データを作る）
- 上のメニュー「Actions」タブを開く。「I understand my workflows, go ahead and enable them」が出たら押す。
- 左の「daily-stock-board」を選び、右の「Run workflow」→「Run workflow」を押す。
- 1〜2分で緑のチェックが付けば成功。`data/` にCSV、`docs/` にPNGとindex.htmlができています。

### 5. ダッシュボードを公開する（GitHub Pages）
- 「Settings」タブ →左メニュー「Pages」。
- 「Build and deployment」の Source を「Deploy from a branch」に。
- Branch を「main」、フォルダを「/docs」にして「Save」。
- 数分後、`https://<あなたのユーザー名>.github.io/kabu-board/` で公開されます。これがnoteに貼るリンクです。

これで完了。以降は**平日17時ごろ（日本時間）に自動更新**されます。

---

## 診断のたびにやること（①②ラインの更新）
`config/stocks.json` の各銘柄の `watch`（①様子見）と `exit`（②撤退）を、その回の診断値に書き換えるだけ。
GitHubのサイト上で `config/stocks.json` を開き、鉛筆マーク（Edit）で直接直せます。保存すれば次回更新から反映されます。

書き換えのルール（カルテの原則どおり）：
- 現在価格 ＞ ①様子見 ＞ ②撤退 の順に必ず下がるように。
- ①様子見は現在値の「下」に置く（直近の押し目の安値あたり）。
- ②撤退は「％」ではなく、チャートの構造的な支持線（節目）に合わせる。

いまの値は暫定です。最初の診断値が決まったら書き換えてください。

## 銘柄を足す・入れ替えるとき
`config/stocks.json` の `stocks` に同じ形でブロックを増やす／減らすだけ。
`ticker` は東証銘柄なら「コード + .T」（例：9432 → `9432.T`）です。

---

## 仕組みのメモ（技術）
- データ元：Yahoo!ファイナンス（`yfinance` 経由）。日足の終値・出来高。
- `scripts/fetch.py`：履歴をまとめて取り直し、既存CSVと重複なく統合して保存（欠損・重複に強い）。
- `scripts/build.py`：CSVと設定からPNG（matplotlib）と動くHTML（plotly）を生成。
- `.github/workflows/daily.yml`：平日17時JST（UTC08:00）に自動実行＋手動実行も可能。
- 日本語の文字化け防止に、実行時 `fonts-noto-cjk` を入れています。

## 注意
- GitHub Actionsの定期実行は混雑時に数十分ずれることがあります（1日1回なので実害はほぼありません）。
- 休場日は新しいデータが無いため、その日はコミットをスキップします（正常動作）。

※本システムはAIの検索および推論に基づく学習用の情報提供であり、投資助言ではありません。
①様子見／②撤退ラインは学習用の目安です。投資判断はご自身の判断と責任で行ってください。
