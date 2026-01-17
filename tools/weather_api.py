import logging
import aiohttp

async def get(self):
        """名古屋市の天気情報を取得する"""
        params = {
            'city': self.city_code
            }
        
        async with aiohttp.ClientSession() as session:
            self.logger.info("天気情報を取得中...")
            
            try: # try-exceptで囲むとより安全です
                async with session.get(self.base_url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        forecast = data['forecasts'][0]
                        
                        # ★ 修正: 成功したこの場所でデータを作って返す
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
                        # 200以外（404など）の場合はここに来る
                        self.logger.error(f"天気情報の取得に失敗しました。Status: {resp.status}")
                        return None

            except Exception as e:
                self.logger.error(f"天気取得中にエラー発生: {e}")
                return None