import const
import discord
import aiohttp
import json
import os

# VOICEVOXの設定
# ソフトを起動しているPCのURL（ローカルならこのままでOK）
VOICEVOX_API_URL = "http://127.0.0.1:50021"
# 話者ID (例: 1=ずんだもんあまあま, 3=ずんだもんノーマル, 2=四国めたんノーマル)
# 変更したい場合はVOICEVOXソフト内のIDを確認してください
SPEAKER_ID = 3

class YOMIAGE:
    def __init__(self, bot, logger=None):
        if logger:
            logger.info('yomiage initialize')
        self.bot = bot
        self.logger = logger
        self.yomi_channel_id = const.YOMIAGE_YOMI_CHANNEL_ID
        if self.logger:
            self.logger.info('読み上げチャンネルシステムのinitialize完了')

    async def generate_voice(self, text):
        """VOICEVOX Engineにテキストを送り、音声データをファイルとして保存する"""
        try:
            async with aiohttp.ClientSession() as session:
                # 1. Audio Query (テキストから音声合成用のパラメータを生成)
                # paramsにtextとspeakerを指定
                query_url = f"{VOICEVOX_API_URL}/audio_query"
                params = {"text": text, "speaker": SPEAKER_ID}
                
                async with session.post(query_url, params=params) as resp:
                    if resp.status != 200:
                        self.logger.error(f"Audio Query Error: {resp.status}")
                        return False
                    query_data = await resp.json()

                # 2. Synthesis (パラメータを元に音声データを生成)
                synthesis_url = f"{VOICEVOX_API_URL}/synthesis"
                synthesis_params = {"speaker": SPEAKER_ID}
                
                # audio_queryで受け取ったjsonをそのまま渡す
                async with session.post(synthesis_url, params=synthesis_params, json=query_data) as resp:
                    if resp.status != 200:
                        self.logger.error(f"Synthesis Error: {resp.status}")
                        return False
                    voice_data = await resp.read()

                # 3. 音声データを一時ファイルとして保存
                with open("temp_voice.wav", "wb") as f:
                    f.write(voice_data)
                
                return True

        except Exception as e:
            self.logger.error(f"VOICEVOX通信エラー: {e}")
            return False

    async def process(self, message: discord.Message):
        # --- 1. チャンネルとBotのフィルタリング ---
        if message.channel.id != self.yomi_channel_id:
            return
        if message.author.bot:
            return

        # --- 2. ボイスチャンネル接続確認 ---
        if not message.guild.voice_client or not message.guild.voice_client.is_connected():
            return

        voice_client = message.guild.voice_client
        text = message.content

        # --- 3. テキストの事前処理（URL省略など） ---
        # 簡易的なURL省略
        if "http" in text:
             text = "ユーアールエルが送信されました"
        
        # ログ出力
        self.logger.info(f"読み上げ開始: {text}")

        # --- 4. 音声生成 ---
        success = await self.generate_voice(text)
        
        if success:
            # --- 5. 再生処理 ---
            # 既に再生中の場合は止める（割り込み再生）
            # ※順番に再生したい場合はQueue(キュー)の実装が必要になります
            if voice_client.is_playing():
                voice_client.stop()

            # FFmpegを使って再生
            # executable='ffmpeg' はパスが通っていれば指定不要ですが、通っていない場合はフルパスを指定してください
            source = discord.FFmpegPCMAudio("temp_voice.wav")
            voice_client.play(source)
        else:
            self.logger.error("音声生成に失敗しました")
            
        return None