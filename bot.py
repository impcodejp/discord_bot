# bot.py
import discord
import os
import logging
from discord.ext import commands
from channel.ai_chatbot import AIChatbot
from tools.throw_ai import GemmaChatbot
import const

class MyBot(commands.Bot):
    def __init__(self, logger):
        self.logger = logger
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

        # AIの初期化 (Cogsからも使えるように self に保持)
        AI_API_KEY = os.getenv('GEMINI_API_KEY')
        self.ai_chatbot = AIChatbot(AI_API_KEY, logger=self.logger)
        self.ai_throw_gemma27 = GemmaChatbot(AI_API_KEY, logger=self.logger)
        self.ai_throw_gemma4 = GemmaChatbot(AI_API_KEY, model_name="gemma-3-4b-it", logger=self.logger)
        self.ai_throw_gemini = GemmaChatbot(AI_API_KEY, model_name="gemini-2.5-flash", logger=self.logger)

        # チャンネルごとのチャットハンドラー
        self.handlers = {
            const.CHAT_CHANNEL_ID: self.ai_chatbot,
        }

    async def setup_hook(self):
        """起動時のセットアップ"""
        # Cogsの読み込み
        await self.load_extension("cogs.utility")
        await self.load_extension("cogs.finance")
        await self.load_extension("cogs.scheduler")
        await self.load_extension("cogs.persona_update")
        
        
        self.logger.info("全Cogsのロード完了")
        
        # コマンド同期
        self.logger.info("スラッシュコマンドの同期実行")
        await self.tree.sync()

    async def on_ready(self):
        self.logger.info(f'Bot({self.user})を起動しました。 (ID: {self.user.id})')

    async def on_message(self, message):
        if message.author == self.user:
            return

        # AIチャット機能 (handler)
        handler = self.handlers.get(message.channel.id)
        if handler:
            response = await handler.process(message)
            if response:
                await message.channel.send(response)

        # コマンド処理
        await self.process_commands(message)

# main.py から呼び出される起動関数
def run_bot(logger, token):
    bot = MyBot(logger)
    bot.run(token)