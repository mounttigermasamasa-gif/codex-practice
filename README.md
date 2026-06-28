# PDF Toolbox

PDF の統合・分割を行うためのツール集です。用途や職場 PC の制約に合わせて、次の 2 種類から選べます。

- **HTML 版 PDF Toolbox Portable**: Python や Node.js などの開発環境がない PC でも、通常のブラウザで `app/index.html` を開くだけで使えます。
- **Python 版 PDF Toolbox Desktop**: Python を利用できる環境向けの Tkinter デスクトップアプリです。ユーザー領域の仮想環境に入れるため、管理者権限なしで使えます。

## HTML 版: PDF Toolbox Portable

職場 PC に Python、Node.js、Java などの開発環境が入っていなくても使える PDF 統合・分割アプリです。管理者権限が必要なインストーラーは使わず、Edge / Chrome などの通常ブラウザで `app/index.html` を開くだけで起動します。

### HTML 版の特徴

- Python、Node.js、Java などのプログラミング環境は不要
- 管理者権限やインストール作業は不要
- Edge / Chrome など、一般的なブラウザで起動
- PDF ファイルを複数選択して 1 つの PDF に統合
- PDF を 1 ページずつ、または `1-3,5,8-10` のようなページ範囲で分割
- 選択した PDF はブラウザ内で処理され、サーバーには送信されません

### HTML 版の使い始める手順

1. このフォルダーを職場 PC のデスクトップやドキュメントなど、書き込み可能な場所へコピーします。
2. `app/index.html` をダブルクリックします。
3. ブラウザで画面が開いたら PDF を選択して統合・分割します。

> 初回起動時に `PDF 処理ライブラリ: 使用可能` と表示されれば利用できます。職場ネットワークで外部 CDN がブロックされる場合は、社内配布用に `pdf-lib.min.js` を同梱した版を配布してください。

### HTML 版で PDF を統合する

1. 「PDF を選択」で統合したい PDF を複数選択します。
2. 一覧の PDF をクリックして選択し、「上へ」「下へ」で順番を調整します。
3. 「統合 PDF を保存」を押すと `merged.pdf` がダウンロードされます。

### HTML 版で PDF を分割する

1. 「分割する PDF を選択」で PDF を 1 つ選択します。
2. 「1ページずつ分割」または「ページ範囲で分割」を選びます。
3. ページ範囲で分割する場合は `1-3,5,8-10` のように入力します。
4. 「PDF を分割して保存」を押すと、分割後の PDF がダウンロードされます。

## Python 版: PDF Toolbox Desktop

Python を利用できる環境向けの、Tkinter ベースの PDF 統合・分割用デスクトップアプリです。PDF 操作には `pypdf` を使用します。

### Python 版の特徴

- PDF ファイルを複数選択して、指定順に 1 つの PDF に統合
- PDF を全ページ単位で分割、または指定ページ範囲ごとに分割
- ユーザー領域の仮想環境にセットアップ可能
- Windows の管理者権限なしで起動可能

### Python 版の必要環境

- Python 3.10 以降
- `pypdf`

### Python 版の管理者権限なしセットアップ

職場 PC などで管理者権限がない場合は、ユーザーフォルダー内に仮想環境を作成してください。

```bash
python -m venv .venv
.venv\\Scripts\\python -m pip install -r requirements.txt
.venv\\Scripts\\python pdf_toolbox.py
```

macOS / Linux の場合:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python pdf_toolbox.py
```

### Python 版で PDF を統合する

1. 「PDF を追加」で統合したい PDF を選びます。
2. 「上へ」「下へ」で統合順を調整します。
3. 「統合 PDF を保存」を押して保存先を選びます。

### Python 版で PDF を分割する

1. 「PDF を選択」で分割したい PDF を 1 つ選びます。
2. 出力フォルダーを選びます。
3. 分割方法を選びます。
   - 「1ページずつ分割」: 各ページを別々の PDF として保存します。
   - 「ページ範囲で分割」: `1-3,5,8-10` のように入力した範囲ごとに保存します。
4. 「PDF を分割」を押します。

## 注意事項

- パスワード保護された PDF や破損した PDF は処理できない場合があります。
- HTML 版の保存先はブラウザのダウンロード設定に従います。
- 大きな PDF を大量に処理すると、PC のメモリ使用量が増える場合があります。
