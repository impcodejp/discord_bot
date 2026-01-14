# Discord AI Assistant Bot

Python製の多機能Discord Botです。Google Gemini AIを活用したチャット機能、毎朝の天気・技術記事通知、レシートの画像解析による家計簿補助機能などを備えています。

## 🚀 主な機能

* **AIチャットボット (Gemma/Gemini)**
    * 特定のチャンネルでメンションなしで会話が可能。
    * 文脈を理解し、親しみやすいキャラクター設定で応答します。
* **毎朝の定期通知 (毎日 7:00 JST)**
    * **天気予報**: 名古屋エリアの天気、降水確率を表示。
    * **Qiitaトレンド**: Pythonに関する注目のQiita記事トップ3を通知。
* **支払い履歴管理 & AIコメント**
    * `/pay_history` コマンドで、Botに送信した支払いメモ（チャット履歴）を集計。
    * **Gemini AI** が履歴データを解析し、CSVファイルを生成。
    * 支出内容に合わせて、AIキャラクターが労いや気遣いのコメントを返してくれます。
* **ロギング機能**
    * 動作ログをコンソールおよびファイル(`logs/`)に自動記録。

## 🛠 使用技術

* **言語**: Python 3.x
* **フレームワーク**: discord.py
* **AI**: Google Gen AI SDK (Gemini / Gemma モデル)
* **その他API**: 天気予報API (Livedoor Weather互換), Qiita API v2

## ⚙️ セットアップ手順

### 1. リポジトリのクローン
```bash
git clone https://github.com/impcodejp/discord_bot.git
cd discord_bot
```

### 2. 仮想環境の作成とライブラリインストール
```bash
# Windowsの場合
python -m venv venv
venv\Scripts\activate

# 必要なライブラリをインストール
pip install discord.py google-genai requests
```

### 3. 環境変数の設定
Botの実行にはAPIキーが必要です。環境変数を設定するか、`.env` ファイル（非推奨、ローカルのみ）などで管理してください。

| 変数名 | 説明 |
| --- | --- |
| `DISCORD_BOT_TOKEN2` | Discord Botのトークン |
| `GEMINI_API_KEY` | Google Gemini APIのキー |

### 4. 起動
```bash
# Windows (batファイルを使用)
start.bat

# または直接Pythonで実行
python -m main
```

## 📁 ディレクトリ構成

* `main.py`: エントリーポイント。ログ設定とBotの起動を行います。
* `bot.py`: Botの本体。コマンド定義や定期タスクを管理。
* `channel/`: 各チャンネルごとの処理ロジック (AIチャットなど)。
* `tools/`: 外部APIやAIとの連携用モジュール (Qiita, Weather, Gemini)。
* `utils/`: ユーティリティ (ログ設定など)。
* `logs/`: 実行ログの保存先 (自動生成)。

## ⚠️ 注意事項

* このBotは `C:\ProgramData\impcode\discord-bot\logs` (または設定されたパス) にログを出力します。
    * 実行環境によっては書き込み権限のエラーが出る場合があるため、その際は `utils/log_config.py` のパスを変更してください。
* 天気予報は現在「名古屋 (230010)」に固定されています。変更する場合は `bot.py` を編集してください。

## License

This project is licensed under the MIT License.