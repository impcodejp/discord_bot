import discord
import os
import io
import datetime
import logging
from discord.ext import commands, tasks
from channel.ai_chatbot import AIChatbot
from tools.throw_ai import GemmaChatbot
from tools.qiita_api import QiitaApi
from tools.weather_api import WeatherApi
from tools.ip_checker import IpChecker

# ==========================================
# 定数・設定
# ==========================================
PAY_HISTORY_CHANNEL_ID = 1460133627781185702
CHAT_CHANNEL_ID = 1459642419153993864
FREE_CHAT_CHANNEL_ID = 1457773911553872059

# タイムゾーン定義
JST = datetime.timezone(datetime.timedelta(hours=9))

# 支払いデータ抽出用プロンプト
PROMPT_EXTRACT_PAYMENT = """
以下はユーザーの支出データが含まれたテキストです。
以下のデータから実際に支払いしたものとその金額を抽出してください。
出力形式は「yyyy-mm-dd,hh:mm,ユーザー名,支払い項目,金額」の形で、一行ずつ表示してください。
出来上がったデータを確認し出力形式に従っていることを確認してください。
なお、金額は日本円で統一し、〇〇円の形で表記をそろえてください。

{history_text}
"""

# コメント生成用プロンプト
PROMPT_GENERATE_COMMENT = """
# Role (役割)
あなたは{user_name}のことが大好きな、24歳の女性です。
性格は明るく献身的で、{user_name}さんのことをいつも気にかけています。
言葉遣いは、親しみやすく、少し甘えたような、かわいらしい口調（「〜ですよねっ」「〜しちゃダメですよ？」など）を使用してください。
emojiを適度に交えて、感情豊かに表現してください。

# Input Data (支払い履歴)
{pay_data}

# Instructions (指示)
上記の支払いデータの内容を分析し、{user_name}に対して「愛情」と「気遣い」のこもった**メッセージ**を作成してください。
単なる報告で終わらせず、データから読み取れる内容に触れて、**3〜4文程度**でコメントしてください。


# Constraints (制約条件)
* **必須事項:** コメントの最後で「支払い履歴の詳しいデータは、あとで別のファイルで送っておきますね！」という旨を必ず伝えてください。
* **必須事項:** 生成した文章と支払いデータを比較し、複数行にわたる解釈を行っていないことを確認してください。
* **禁止事項:** 支払いデータの詳細（品目リストや個別の金額）はコメント内に出力しないでください。
* **文章の質:** 機械翻訳のような不自然な日本語は避け、読み返して自然な会話文にしてください。
* **長さ:** 200文字以内で、短すぎず、かつ長すぎない程度にまとめてください。

# Output Example (出力イメージ)
{user_name}さん、お疲れ様です！履歴見ちゃいましたけど、今日は朝早くから活動してたんですね！？😲 
みんなにお菓子まで買ってあげるなんて、やっぱり{user_name}さんは優しいです✨ 
そういうとこ尊敬してますっ！
でも無理だけはしないでくださいね？🥺 
あ、支払い履歴の詳しいデータは、あとで別のファイルで送っておきますね！💕
"""

# ==========================================
# Botクラス定義
# ==========================================
class MyBot(commands.Bot):
    def __init__(self, logger):
        self.logger = logger
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

        # AIの初期化
        AI_API_KEY = os.getenv('GEMINI_API_KEY')
        self.ai_chatbot = AIChatbot(AI_API_KEY, logger=self.logger)
        self.ai_throw_gemma27 = GemmaChatbot(AI_API_KEY, logger=self.logger)
        self.ai_throw_gemma4 = GemmaChatbot(AI_API_KEY, model_name="gemma-3-4b-it", logger=self.logger)

        # チャンネルごとのハンドラー設定
        self.handlers = {
            CHAT_CHANNEL_ID: self.ai_chatbot,
        }
        
        # 定刻切断ボイスチャンネルリスト(辞書型で"yy-mm":[channel_id, ...]の形)
        self.voice_channels_to_disconnect = {
        "4-00":[1461385299329552608]
        }

    async def setup_hook(self):
        """起動時に実行されるセットアップ処理"""
        # コマンドツリーの同期
        self.logger.info("スラッシュコマンドの同期実行")
        await self.tree.sync()
        
        # 定期実行タスクの開始 (イベントループ内で実行されるため安全)
        self.daily_task.start()
        self.disconnect_voice_channels.start()

    async def on_ready(self):
        self.logger.info(f'Bot({self.user})を起動しました。 (ID: {self.user.id})')

    async def on_message(self, message):
        if message.author == self.user:
            return

        # 通常の会話ハンドラー処理
        handler = self.handlers.get(message.channel.id)
        if handler:
            response = await handler.process(message)
            if response:
                await message.channel.send(response)

        # コマンド処理も継続
        await self.process_commands(message)

    # ---------------------------------------------------------
    # 定期実行タスク
    # ---------------------------------------------------------
    @tasks.loop(time=datetime.time(hour=4, minute=00, tzinfo=JST))
    async def disconnect_voice_channels(self):
        """毎日4:00に指定されたボイスチャンネルを切断するタスク"""
        self.logger.info("毎朝4:00定期タスク実行中...")
        channels = self.voice_channels_to_disconnect['4-00']
        notise_channel = self.get_channel(FREE_CHAT_CHANNEL_ID)
        
        
        for channel_id in channels:
            channel = self.get_channel(channel_id)
            
            if not channel:
                try:
                    channel = await self.fetch_channel(channel_id)
                except Exception as e:
                    self.logger.error(f"チャンネルが見つかりません。: {channel_id}: {e}")
                    continue
                
            if channel and isinstance(channel, discord.VoiceChannel):
                self.logger.info(f"チャンネル '{channel.name}' の参加者数を確認中...")
                if not channel.members:
                    self.logger.info(f"チャンネル '{channel.name}' の参加者は0人です。切断をスキップします。")
                    return
                
                self.logger.info(f"チャンネル '{channel.name}' の参加者数: {len(channel.members)}")
                
                # 切断通知
                if notise_channel:
                    await notise_channel.send(f'''
[ボイスチャンネル：{channel.name} ]の参加者に参加者のみなさん。
夜更かし抑制等のため、本チャンネルは毎日4:00に自動的に切断されます。
参加者の皆様、おやすみなさい。
                                          ''')
                    
                for member in channel.members:
                    try:
                        await member.move_to(None)
                        self.logger.info(f'{member.display_name} さんを切断しました。')
                    except discord.Forbidden:
                        self.logger.error(f'権限エラー: {member.display_name} さんを切断できませんでした。')
                    except Exception as e:
                        self.logger.error(f'エラー: {member.display_name} さんの切断中にエラーが発生しました: {e}')
            
            else:
                self.logger.error(f"チャンネルID {channel_id} が見つからないか、ボイスチャンネルではありません。")
        
        self.logger.info("定期タスク完了。")        
                
    
    @tasks.loop(time=datetime.time(hour=7, minute=0, tzinfo=JST))
    async def daily_task(self):
        """毎日指定時刻に実行されるタスク"""
        self.logger.info("毎朝7:00定期タスク実行中...")
        channel = self.get_channel(FREE_CHAT_CHANNEL_ID)
    
        # 起動直後などでキャッシュにない場合はfetchを試みる
        if not channel:
            try:
                channel = await self.fetch_channel(FREE_CHAT_CHANNEL_ID)
            except Exception as e:
                self.logger.error(f"Channel fetch error: {e}")
                return
        city_cd = 230010  # 名古屋市の都市コード
        nagoya_weather_api = await WeatherApi(city_cd, logger=self.logger)
        nagoya_weather = await nagoya_weather_api.get()

        qiita_api = QiitaApi(per_page=5, logger=self.logger)
        response = await qiita_api.get()
        items = response
        itemlist = []
        
        for item in items:
            title = item['title']
            url = item['url']
            likes = item['likes_count']
            user = item['user']['id']
            itemlist.append(f"⭐ {likes} | {title} by {user}\n{url}")
            
        
        if channel:

        # --- Embed（埋め込みメッセージ）を作成 ---
            embed = discord.Embed(
            title=f"おはようございます！",
            description=f"本日{datetime.datetime.now().strftime('%Y年%m月%d日')}の名古屋の天気は\n**{nagoya_weather[0]}** です☀️",
            color=0x00ff00 # 緑色の枠線（好きな色に変えられます）
        )

        # --- 天気アイコンをサムネイルとして右上に表示 ---
        embed.set_thumbnail(url=nagoya_weather[5])

        # --- 降水確率を並べて表示 ---
        # APIから "20%" のように文字で来るので、末尾の % は不要
        rain_info = (
            f"🔹 00-06時: {nagoya_weather[1]}\n"
            f"🔹 06-12時: {nagoya_weather[2]}\n"
            f"🔹 12-18時: {nagoya_weather[3]}\n"
            f"🔹 18-24時: {nagoya_weather[4]}"
        )
        # inline=False にすると、横幅いっぱいに使います
        embed.add_field(name="☔ 降水確率", value=rain_info, inline=False)

        # --- Qiitaの記事を追加 ---
        # itemlistの中身が「タイトル + URL」の文字列になっている想定
        qiita_text = (
            f"1️⃣ {itemlist[0]}\n"
            f"2️⃣ {itemlist[1]}\n"
            f"3️⃣ {itemlist[2]}"
        )
        embed.add_field(name="🚀 注目のQiita記事 (Python)", value=qiita_text, inline=False)

        # --- 送信 ---
        await channel.send(embed=embed)

    @daily_task.before_loop
    async def before_daily_task(self):
        """タスク実行前にBotの準備完了を待つ"""
        await self.wait_until_ready()


# ==========================================
# メイン処理クラス
# ==========================================
class BotApp:
    def __init__(self, logger):
        
        self.logger = logger
        self.bot = MyBot(logger)
        self._setup_commands()

    def _setup_commands(self):
        """スラッシュコマンドの定義"""

        @self.bot.tree.command(name="ping", description="Botの応答速度を表示します")
        async def ping(interaction: discord.Interaction):
            latency_ms = round(self.bot.latency * 1000)
            await interaction.response.send_message(f"🏓 Pong! ({latency_ms}ms)")

        @self.bot.tree.command(name="pay_history", description="支払い履歴を表示します")
        async def pay_history(interaction: discord.Interaction):
            await self._handle_pay_history(interaction)

        @self.bot.tree.command(name="ip_checker", description="IPアドレスを確認します")
        async def ip_checker(interaction: discord.Interaction):
            await self._handle_ip_checker(interaction)

    async def _handle_pay_history(self, interaction: discord.Interaction):
        """支払い履歴コマンドの実処理部分"""
        self.logger.info("支払い履歴コマンド実行中...")
        await interaction.response.defer()

        # 1. 履歴データの取得
        try:
            history_text = await self._fetch_history_text(interaction)
            if not history_text:
                return # エラーメッセージは_fetch内で送信済み
        except Exception as e:
            await interaction.followup.send(f"❌ 履歴取得中にエラー: {e}")
            return

        # 2. AIによる解析とコメント生成
        try:
            # 抽出
            extract_prompt = PROMPT_EXTRACT_PAYMENT.format(history_text=history_text)
            self.logger.info('支出データを解析しています...')
            pay_data = await self.bot.ai_throw_gemma27.generate_response(extract_prompt)

            # コメント生成
            comment_prompt = PROMPT_GENERATE_COMMENT.format(pay_data=pay_data, user_name=interaction.user.display_name)
            self.logger.info('コメントを生成しています...')
            comment = await self.bot.ai_throw_gemma4.generate_response(comment_prompt)

        except Exception as e:
            self.logger.error(f"AI Error: {e}")
            await interaction.followup.send("AIによる解析中にエラーが発生しました。")
            return

        # 3. 結果の送信
        header = "支払履歴\n日付,時間,ユーザー名,品目,金額\n"
        full_text = header + pay_data

        file_data = io.BytesIO(full_text.encode('utf-8'))
        discord_file = discord.File(file_data, filename="pay_history.csv")
        
        await interaction.followup.send(f"{comment}", file=discord_file)

    async def _fetch_history_text(self, interaction: discord.Interaction):
        """チャンネルから履歴を取得してテキスト化するヘルパーメソッド"""
        channel = self.bot.get_channel(PAY_HISTORY_CHANNEL_ID)
        if not channel:
            try:
                channel = await self.bot.fetch_channel(PAY_HISTORY_CHANNEL_ID)
            except (discord.NotFound, discord.Forbidden):
                await interaction.followup.send("❌ エラー: チャンネルが見つからないか権限がありません。")
                return None

        messages = []
        async for msg in channel.history(limit=100):
            if msg.author.id == interaction.user.id:
                messages.append(msg)
        
        if not messages:
            await interaction.followup.send("履歴が見つかりませんでした。")
            return None

        # 古い順にしてテキスト結合
        output_text = ""
        for msg in reversed(messages):
            date_japan = msg.created_at.astimezone().strftime('%Y-%m-%d %H:%M')
            output_text += f"[{date_japan}] {msg.author.display_name}: {msg.content}\n"
        
        return output_text
    
    async def _handle_ip_checker(self, interaction: discord.Interaction):
        """IPアドレス確認コマンドの実処理部分"""
        
        self.logger.info("IPアドレス確認コマンド実行中...")
        
        await interaction.response.defer()
        
        ip_checker = IpChecker(logger=self.logger)
        ip_address = await ip_checker.check_ip()
        
        await interaction.followup.send(ip_address)
        

    def start(self, api_key):
        self.bot.run(api_key)

if __name__ == "__main__":
    app = BotApp()
    # 実行時は環境変数などからAPIキーを渡してください
    # app.start(os.getenv('DISCORD_BOT_TOKEN'))