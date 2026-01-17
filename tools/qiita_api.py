import aiohttp
import logging

class QiitaApi:
    """Qiita APIを利用して記事情報を取得するクラス"""
    
    BASE_URL = "https://qiita.com/api/v2/items"
    
    def __init__(self, per_page=20, logger=None):
        self.logger = logger
        self.per_page = per_page
        self.logger.info('QiitaAPI 初期化完了')
    
    async def get(self):
        """Qiitaから最新の記事情報を取得する"""
        self.logger.info('Qiita記事を取得中...')
        
        params = {
            'per_page': self.per_page,
            'page': 1,
            'query': 'tag:python stocks:>=30'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.BASE_URL, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.logger.info('Qiita記事の取得完了')
                        return data
                    else:
                        self.logger.error(f"Failed to get Qiita articles, status code: {resp.status}")
                        return None

        except aiohttp.ClientError as e:
            self.logger.error(f"通信エラーが発生しました: {e}")
            return None
        except Exception as e:
            self.logger.error(f"予期せぬエラー: {e}")
            return None