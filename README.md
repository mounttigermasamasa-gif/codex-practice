# PDF Toolbox Desktop

管理者権限なしで使える、PDF の統合・分割用デスクトップアプリです。Python 標準の Tkinter で画面を作り、PDF 操作には `pypdf`、Web ページ全体の PDF 保存には `playwright` を使用します。

## 特徴

- PDF ファイルを複数選択して、指定順に 1 つの PDF に統合
- PDF を全ページ単位で分割、または指定ページ範囲ごとに分割
- Web ページ内のファイルリンク先データを、PDF・Word・画像など複数の形式指定で一括ダウンロード
- Web ページ全体を画面表示に近いレイアウトで PDF 保存
- インストール先を選ばないポータブル構成
- Windows の管理者権限なしで起動可能

## 必要環境

- Python 3.10 以降
- `pypdf`
- `playwright`（Web ページ全体の PDF 保存に使用）

## 管理者権限なしでのセットアップ

職場 PC などで管理者権限がない場合は、ユーザーフォルダー内に仮想環境を作成してください。

```bash
python -m venv .venv
.venv\\Scripts\\python -m pip install -r requirements.txt
.venv\\Scripts\\python -m playwright install chromium
.venv\\Scripts\\python pdf_toolbox.py
```

macOS / Linux の場合:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python -m playwright install chromium
./.venv/bin/python pdf_toolbox.py
```

## ワンクリック起動（Windows）

セットアップ後は、リポジトリ直下の `start_pdf_toolbox.bat` をダブルクリックするとアプリを起動できます。

この起動ファイルは、まず `.venv\Scripts\pythonw.exe` を探し、見つからない場合は PC にインストール済みの Python ランチャーや `pythonw.exe` / `python.exe` を順番に探して `pdf_toolbox.py` を起動します。

## 使い方

### PDF の統合

1. 「PDF を追加」で統合したい PDF を選びます。
2. 「上へ」「下へ」で統合順を調整します。
3. 「統合 PDF を保存」を押して保存先を選びます。

### Web ファイル保存

1. 「Web ファイル保存」タブを開きます。
2. ダウンロードしたいファイルリンクがある Web ページの URL を入力します。
3. 保存フォルダーを選びます。
4. 「取得するファイル形式」で PDF、Word、Excel/CSV、PowerPoint、テキスト、画像、圧縮ファイル、動画・音声、実行/ディスクイメージから必要な形式を複数選びます。
5. 「ファイルリンクを一括ダウンロード」を押します。

選択した形式に該当し、直接ファイルを指すリンクだけを保存します。ブラウザーで現在開いているページは自動取得できないため、対象ページの URL をコピーして入力してください。

### Web ページ全体の PDF 保存

1. 「Web ファイル保存」タブを開きます。
2. PDF 保存したい Web ページの URL を入力します。
3. 「Web ページ全体を PDF 保存」を押し、保存先を選びます。

この機能は Chromium を使ってページ全体をレンダリングし、背景色や画像を含めて PDF 化します。初回セットアップ時に `python -m playwright install chromium` を実行してください。

### PDF の分割

1. 「PDF を選択」で分割したい PDF を 1 つ選びます。
2. 出力フォルダーを選びます。
3. 分割方法を選びます。
   - 「1ページずつ分割」: 各ページを別々の PDF として保存します。
   - 「ページ範囲で分割」: `1-3,5,8-10` のように入力した範囲ごとに保存します。
4. 「PDF を分割」を押します。

## 注意

パスワード保護された PDF や破損した PDF は処理できない場合があります。
