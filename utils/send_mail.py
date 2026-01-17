import smtplib
import os
from email.mime.text import MIMEText
from email.utils import formatdate
import logging
from typing import Optional
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# 送信元の設定 (さくらインターネット)
SAKURA_EMAIL = os.getenv("SAKURA_EMAIL")      # あなたのメールアドレス
SAKURA_PASSWORD = os.getenv("SAKURA_PASSWORD")      # メールパスワード
SAKURA_SMTP_HOST = os.getenv("SAKURA_SMTP_HOST")    # SMTPサーバー (初期ドメイン推奨)

# ==========================================
# 1. SakuraMailSender クラス定義
# ==========================================
class SakuraMailSender:
    def __init__(self, smtp_port: int = 587, logger: Optional[logging.Logger] = None):
        """
        さくらメール送信クラスの初期化
        """
        self.email_address = SAKURA_EMAIL
        self.password = SAKURA_PASSWORD
        self.smtp_host = SAKURA_SMTP_HOST
        self.smtp_port = smtp_port
        self.logger = logger

    def send(self, subject: str, body: str) -> bool:
        """
        メールを送信するメソッド
        """
        
        to_email = os.getenv("TO_EMAIL")
        
        # メールの作成
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = self.email_address
        msg['To'] = to_email
        msg['Date'] = formatdate()

        if self.logger:
            self.logger.info(f"メール送信開始: To={to_email}, Subject={subject}")

        smtpobj = None
        try:
            # サーバー接続
            smtpobj = smtplib.SMTP(self.smtp_host, self.smtp_port)
            smtpobj.ehlo()
            smtpobj.starttls()  # 暗号化
            smtpobj.ehlo()
            
            # ログイン
            smtpobj.login(self.email_address, self.password)
            
            # 送信
            smtpobj.sendmail(self.email_address, to_email, msg.as_string())
            
            if self.logger:
                self.logger.info("メール送信成功")
            return True

        except Exception as e:
            error_msg = f"メール送信エラー: {e}"
            if self.logger:
                self.logger.error(error_msg)
            else:
                print(error_msg)
            return False
        
        finally:
            if smtpobj:
                smtpobj.close()

# ==========================================
# 2. 実行用 main 関数
# ==========================================
def main():
    # ログの設定（画面に見やすく表示するため）
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    print("--- メール送信テストを開始します ---")

    # 1. クラスの初期化
    sender = SakuraMailSender(
        logger=logger
    )

    # 2. テストメールの内容作成
    subject = "【テスト】Pythonからのメール送信テスト"
    body = """
これは SakuraMailSender クラスの動作確認メールです。

このメールが届いていれば、以下の機能が正常に動作しています。
・SMTPサーバーへの接続
・認証（ログイン）
・メール送信

以上
    """

    # 3. 送信実行
    print("送信中...")
    
    success = sender.send(
        subject=subject,
        body=body
    )

    # 4. 結果表示
    print("-" * 30)
    if success:
        print("✅ テスト完了: メール送信に成功しました！")
    else:
        print("❌ テスト完了: メール送信に失敗しました。設定値やログを確認してください。")
    print("-" * 30)

if __name__ == "__main__":
    main()