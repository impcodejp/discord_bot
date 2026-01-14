import discord
import os
import io
from discord.ext import commands
from channel.ai_chatbot import AIChatbot
from tools.throw_ai import GemmaChatbot

# ==========================================
# 定数・設定 (プロンプトやIDはここで管理)
# ==========================================
PAY_HISTORY_CHANNEL_ID = 1460133627781185702
CHAT_CHANNEL_ID = 1459642419153993864

# 支払いデータ抽出用プロンプト
PROMPT_EXTRACT_PAYMENT = """
以下はユーザーの支出データが含まれたテキストです。
以下のデータから実際に支払いしたものとその金額を抽出してください。
出力形式は「yyyy-mm-dd,hh:mm,ユーザー名,支払い項目,金額」の形で、一行ずつ表示してください。
出来上がったデータを確認し出力形式に従っていることを確認してください。
なお、金額は日本円で統一し、〇〇円の形で表記をそろえてください。

{history_text}
"""

# コメント生成用プロンプト (最新版)
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
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

        # AIの初期化
        AI_API_KEY = os.getenv('GEMINI_API_KEY')
        self.ai_chatbot = AIChatbot(AI_API_KEY)
        self.ai_throw_gemma27 = GemmaChatbot(AI_API_KEY)
        self.ai_throw_gemma4 = GemmaChatbot(AI_API_KEY, model_name="gemma-3-4b-it")

        # チャンネルごとのハンドラー設定
        self.handlers = {
            CHAT_CHANNEL_ID: self.ai_chatbot,
        }

    async def setup_hook(self):
        """起動時に実行されるセットアップ処理"""
        # コマンドツリーの同期
        await self.tree.sync()
        print("Slash commands synced.")

    async def on_ready(self):
        print(f'Bot logged in as {self.user} (ID: {self.user.id})')

    async def on_message(self, message):
        if message.author == self.user:
            return

        # 通常の会話ハンドラー処理
        handler = self.handlers.get(message.channel.id)
        if handler:
            print(f"[{message.channel.name}] {message.author}: {message.content}")
            response = await handler.process(message)
            if response:
                await message.channel.send(response)

        # コマンド処理も継続
        await self.process_commands(message)


# ==========================================
# メイン処理クラス
# ==========================================
class BotApp:
    def __init__(self):
        self.bot = MyBot()
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

    async def _handle_pay_history(self, interaction: discord.Interaction):
        """支払い履歴コマンドの実処理部分"""
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
            print('支出データを解析しています...')
            pay_data = await self.bot.ai_throw_gemma27.generate_response(extract_prompt)

            # コメント生成
            comment_prompt = PROMPT_GENERATE_COMMENT.format(pay_data=pay_data, user_name=interaction.user.display_name)
            print('コメントを生成しています...')
            comment = await self.bot.ai_throw_gemma4.generate_response(comment_prompt)

        except Exception as e:
            print(f"AI Error: {e}")
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

    def start(self, api_key):
        self.bot.run(api_key)

if __name__ == "__main__":
    app = BotApp()
    # 実行時は環境変数などからAPIキーを渡してください
    # app.start(os.getenv('DISCORD_BOT_TOKEN'))