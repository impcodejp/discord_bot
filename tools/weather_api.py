import requests
import logging

class WeatherApi:
    def __init__(self, city_code: int, logger=None):
        self.logger = logger
        self.city_code = str(city_code)
        self.base_url = "https://weather.tsukumijima.net/api/forecast"
        
        self.logger.info(f"名古屋用天気取得Api 初期化完了: city_code={self.city_code}")
    def get(self):
        """名古屋市の天気情報を取得する"""
        params = {
            'city': self.city_code
            }
        response = requests.get(self.base_url, params=params)
        response = response.json()
        weather_data = []
        weather_data.append(response['forecasts'][0]['detail']['weather'])
        weather_data.append(response['forecasts'][0]['chanceOfRain']['T00_06'])
        weather_data.append(response['forecasts'][0]['chanceOfRain']['T06_12'])
        weather_data.append(response['forecasts'][0]['chanceOfRain']['T12_18'])
        weather_data.append(response['forecasts'][0]['chanceOfRain']['T18_24'])
        weather_data.append(response['forecasts'][0]['image']['url'])
        return weather_data