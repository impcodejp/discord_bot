import os
import logging
from utils.log_config import setup_logging
from bot import run_bot


class Main:
    def __init__(self):
        setup_logging()
        self.logger = logging.getLogger(__name__)
        self.logger.info("システム起動処理実施...")
        
    def run(self):
        self.logger.info("メインアプリケーションを実行中...")

        try:
            self.discord_api_key = os.getenv("DISCORD_BOT_TOKEN2")
            if not self.discord_api_key:
                raise ValueError("DISCORD_BOT_TOKEN2 environment variable is not set")
        except Exception as e:
            self.logger.error(f"Error getting API key: {e}")
            return
        
        self.logger.info(f"Discord APIキー: {self.discord_api_key[:4]}****")
        
        run_bot(self.logger, self.discord_api_key)

if __name__ == "__main__":
    main_instance = Main()
    main_instance.run()
    