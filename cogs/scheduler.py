# cogs/scheduler.py
import discord
import datetime
from discord.ext import commands, tasks
from tools.weather_api import WeatherApi
from tools.qiita_api import QiitaApi
import const

class Scheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
        # タスクを開始
        self.daily_task.start()
        self.disconnect_voice_channels.start()

    def cog_unload(self):
        self.daily_task.cancel()
        self.disconnect_voice_channels.cancel()

    @tasks.loop(time=datetime.time(hour=4, minute=00, tzinfo=const.JST))
    async def disconnect_voice_channels(self):
        self.logger.info("毎朝4:00定期タスク実行中...")
        channels_to_check = const.VOICE_CHANNELS_TO_DISCONNECT['4-00']
        notice_channel = self.bot.get_channel(const.FREE_CHAT_CHANNEL_ID)
        
        for channel_id in channels_to_check:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                try:
                    channel = await self.bot.fetch_channel(channel_id)
                except Exception as e:
                    self.logger.error(f"チャンネルが見つかりません。: {channel_id}: {e}")
                    continue
                
            if channel and isinstance(channel, discord.VoiceChannel):
                if not channel.members:
                    return
                
                # 切断通知
                if notice_channel:
                    await notice_channel.send(f'''
[ボイスチャンネル：{channel.name} ]の参加者の皆様。
夜更かし抑制等のため、本チャンネルは毎日4:00に自動的に切断されます。
おやすみなさい。
''')
                    
                for member in channel.members:
                    try:
                        await member.move_to(None)
                        self.logger.info(f'{member.display_name} さんを切断しました。')
                    except Exception as e:
                        self.logger.error(f'切断エラー: {e}')

    @tasks.loop(time=datetime.time(hour=7, minute=0, tzinfo=const.JST))
    async def daily_task(self):
        self.logger.info("毎朝7:00定期タスク実行中...")
        channel = self.bot.get_channel(const.FREE_CHAT_CHANNEL_ID)
    
        if not channel:
            try:
                channel = await self.bot.fetch_channel(const.FREE_CHAT_CHANNEL_ID)
            except Exception as e:
                self.logger.error(f"Channel fetch error: {e}")
                return

        # 天気取得
        nagoya_weather_api = WeatherApi(230010, logger=self.logger)
        nagoya_weather = await nagoya_weather_api.get()

        # Qiita取得
        qiita_api = QiitaApi(per_page=5, logger=self.logger)
        items = await qiita_api.get()
        itemlist = []
        if items:
            for item in items:
                title = item['title']
                url = item['url']
                likes = item['likes_count']
                itemlist.append(f"⭐ {likes} | {title}\n{url}")
        
        if nagoya_weather is None:
            base_description = "本日の名古屋の天気情報を取得できませんでした。"
            base_rain_info = (
                "🔹 00-06時: 情報なし\n"
                "🔹 06-12時: 情報なし\n"
                "🔹 12-18時: 情報なし\n"
                "🔹 18-24時: 情報なし"
            )
        else:   
            base_description = f"本日{datetime.datetime.now().strftime('%Y年%m月%d日')}の名古屋の天気は\n**{nagoya_weather[0]}** です☀️"
            base_rain_info = (
                f"🔹 00-06時: {nagoya_weather[1]}\n"
                f"🔹 06-12時: {nagoya_weather[2]}\n"
                f"🔹 12-18時: {nagoya_weather[3]}\n"
                f"🔹 18-24時: {nagoya_weather[4]}"
            )

        if channel:
            embed = discord.Embed(
                title=f"おはようございます！",
                description=base_description,
                color=0x00ff00
            )

            rain_info = base_rain_info
            embed.add_field(name="☔ 降水確率", value=rain_info, inline=False)

            if itemlist:
                qiita_text = f"1️⃣ {itemlist[0]}\n2️⃣ {itemlist[1]}\n3️⃣ {itemlist[2]}"
                embed.add_field(name="🚀 注目のQiita記事 (Python)", value=qiita_text, inline=False)

            await channel.send(embed=embed)

    @daily_task.before_loop
    async def before_daily_task(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Scheduler(bot))