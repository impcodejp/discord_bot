import const
import discord
import aiohttp
import json
import os

# VOICEVOXの設定
VOICEVOX_API_URL = "http://127.0.0.1:50021"
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
        self.logger.info(f"--- [DEBUG] 音声生成開始: {text} ---")
        
        try:
            async with aiohttp.ClientSession() as session:
                # 1. Audio Query
                query_url = f"{VOICEVOX_API_URL}/audio_query"
                params = {"text": text, "speaker": SPEAKER_ID}
                
                self.logger.info(f"[DEBUG] Audio Query送信: {query_url}")
                async with session.post(query_url, params=params) as resp:
                    if resp.status != 200:
                        self.logger.error(f"[ERROR] Audio Query失敗 Status: {resp.status}")
                        return False
                    query_data = await resp.json()
                    self.logger.info("[DEBUG] Audio Query成功")

                # 2. Synthesis
                synthesis_url = f"{VOICEVOX_API_URL}/synthesis"
                synthesis_params = {"speaker": SPEAKER_ID}
                
                self.logger.info(f"[DEBUG] Synthesis送信: {synthesis_url}")
                async with session.post(synthesis_url, params=synthesis_params, json=query_data) as resp:
                    if resp.status != 200:
                        self.logger.error(f"[ERROR] Synthesis失敗 Status: {resp.status}")
                        return False
                    voice_data = await resp.read()
                    self.logger.info(f"[DEBUG] Synthesis成功 データサイズ: {len(voice_data)} bytes")

                # 3. ファイル保存
                filename = "temp_voice.wav"
                with open(filename, "wb") as f:
                    f.write(voice_data)
                
                # ファイルが正しく保存されたか確認
                if os.path.exists(filename):
                    file_size = os.path.getsize(filename)
                    self.logger.info(f"[DEBUG] ファイル保存完了: {filename} (サイズ: {file_size} bytes)")
                    if file_size == 0:
                        self.logger.error("[ERROR] 保存されたファイルが空です")
                        return False
                else:
                    self.logger.error("[ERROR] ファイルが見つかりません")
                    return False
                
                return True

        except aiohttp.ClientConnectorError:
            self.logger.error(f"[ERROR] VOICEVOXに接続できません。アプリは起動していますか？ URL: {VOICEVOX_API_URL}")
            return False
        except Exception as e:
            self.logger.error(f"[ERROR] VOICEVOX通信/保存中の予期せぬエラー: {e}")
            return False

    async def process(self, message: discord.Message):
        # ログ過多を防ぐため、対象外の場合は静かにreturnする
        if message.channel.id != self.yomi_channel_id:
            return
        if message.author.bot:
            return

        self.logger.info(f"--- [DEBUG] メッセージ受信: {message.content} ---")

        # ボイスチャンネル接続確認
        voice_client = message.guild.voice_client
        if not voice_client:
            self.logger.info("[DEBUG] Botはボイスチャンネルに接続していません (voice_client is None)")
            return
        
        if not voice_client.is_connected():
            self.logger.info("[DEBUG] Botは切断状態です (is_connected() is False)")
            return

        self.logger.info("[DEBUG] BotはVC接続済み。処理を継続します。")

        text = message.content
        # URL省略
        if "http" in text:
             text = "ユーアールエルが送信されました"

        # 音声生成実行
        success = await self.generate_voice(text)
        
        if success:
            # 再生処理
            if voice_client.is_playing():
                self.logger.info("[DEBUG] 再生中の音声を停止します")
                voice_client.stop()

            self.logger.info("[DEBUG] FFmpegで再生準備開始")
            
            try:
                # 再生完了時のコールバック関数
                def after_playing(error):
                    if error:
                        self.logger.error(f"[ERROR] 再生中にエラーが発生: {error}")
                    else:
                        self.logger.info("[DEBUG] 再生完了")

                # FFmpegソースの作成
                source = discord.FFmpegPCMAudio("temp_voice.wav")
                voice_client.play(source, after=after_playing)
                self.logger.info("[DEBUG] playメソッドを実行しました")

            except Exception as e:
                self.logger.error(f"[ERROR] FFmpeg再生エラー: {e}")
                self.logger.error("ヒント: ffmpegがインストールされていないか、PATHが通っていない可能性があります。")
        else:
            self.logger.error("[ERROR] 音声生成フローが失敗したため再生しません")
            
        return None