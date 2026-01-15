import requests
import json

class QiitaApi:
    """Qiita APIを利用して記事情報を取得するクラス"""
    
    BASE_URL = "https://qiita.com/api/v2/items"
    
    def __init__(self, per_page=20, logger=None):
        self.logger = logger
        self.per_page = per_page
        self.logger.info('QiitaAPI 初期化完了')
    
    def get(self):
        """Qiitaから最新の記事情報を取得する"""
        self.logger.info('Qiita記事を取得中...')
        params = {
            'per_page': self.per_page,
            'page': 1,
            'query': 'tag:python stocks:>=30'
        }
        response = requests.get(self.BASE_URL, params=params)
        response.raise_for_status()
        return response.json()