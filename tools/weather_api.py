import logging
import aiohttp

class WeatherApi:
    def __init__(self, city_code: int, logger=None):
        self.logger = logger
        self.city_code = str(city_code)
        self.base_url = "https://weather.tsukumijima.net/api/forecast"
        
        self.logger.info(f"名古屋用天気取得Api 初期化完了: city_code={self.city_code}")
    async def get(self):
        """名古屋市の天気情報を取得する"""
        params = {
            'city': self.city_code
            }
        
        async with aiohttp.ClientSession() as session:
            self.logger.info("天気情報を取得中...")
            
            async with session.get(self.base_url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    forecast = data['forecasts'][0]
            
            if forecast:
                weather_data = []
                weather_data.append(forecast['detail']['weather'])
                weather_data.append(forecast['chanceOfRain']['T00_06'])
                weather_data.append(forecast['chanceOfRain']['T06_12'])
                weather_data.append(forecast['chanceOfRain']['T12_18'])
                weather_data.append(forecast['chanceOfRain']['T18_24'])
                weather_data.append(forecast['image']['url'])
                self.logger.info("天気情報の取得に成功しました。")
                return weather_data
            else:
                self.logger.error("天気情報の取得に失敗しました。")
                return None