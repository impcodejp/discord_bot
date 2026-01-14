import logging
import logging.handlers
import os
import sys

def setup_logging():
    """
    ログ設定を初期化する関数
    - コンソール出力 (INFOレベル以上)
    - ファイル出力 (INFOレベル以上, ローテーション付き)
    """
    # ログ保存用ディレクトリを作成
    log_dir = "C:\\ProgramData\\impcode\\discord-bot\\logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # ルートロガーの設定
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # フォーマットの設定（日付 時刻 レベル モジュール名 メッセージ）
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 1. コンソール出力ハンドラー
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # 2. ファイル出力ハンドラー（ローテーション付き）
    # bot.log というファイルに書き込み、1MBを超えたらバックアップを作成（最大5ファイルまで）
    file_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, 'bot.log'),
        maxBytes=1_000_000, # 1MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logging.info("ロガーの初期化が完了しました。")