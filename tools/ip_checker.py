import aiohttp
from utils.send_mail import SakuraMailSender

class IpChecker:
    def __init__(self, logger=None):
        self.logger = logger
        
    async def check_ip(self):
        """ユーザーのIPアドレスを確認して返す"""
        self.logger.info("IPアドレスを確認中...")           
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.ipify.org?format=json') as resp:
                if resp.status == 200:
                    data = await resp.json()
                    parts = data['ip'].split('.')
                    padded_parts = [part.zfill(3) for part in parts]
                    padded_ip = '.'.join(padded_parts)
                    self.logger.info(f"取得したIPアドレス: {padded_ip[:8]}***.***")
                    mail_sender = SakuraMailSender(logger=self.logger)
                    subject = "【通知】botサーバのIPアドレス確認"
                    body = f"""
                    discordサーバから、botサーバのIPアドレスは通知依頼がありました。
                    botサーバのある環境のグローバルIPは {data['ip']}です。
                    """
                    result = mail_sender.send(subject=subject, body=body)
                    if result:
                        self.logger.info('IPアドレス通知メールを送信成功')
                        result_str = 'IPアドレス通知メールの送信に成功しました'
                    else:
                        self.logger.error('IPアドレス通知メールの送信失敗')
                        result_str = 'IPアドレス通知メールの送信に失敗しました。'
                    
                    return fr"""
botサーバのIPアドレスは {padded_ip[:8]}\*\*\*.\*\*\*です
{result_str}
                """
                    
                else:
                    self.logger.error(f"Failed to get IP address, status code: {resp.status}")
                    return "IPアドレスの取得に失敗しました。"
        