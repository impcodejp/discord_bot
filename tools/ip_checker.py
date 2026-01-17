import aiohttp

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
                    return fr"botサーバのIPアドレスは {padded_ip[:8]}\*\*\*.\*\*\*です"
                    
                else:
                    self.logger.error(f"Failed to get IP address, status code: {resp.status}")
                    return "IPアドレスの取得に失敗しました。"
        