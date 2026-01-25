import discord
import os
from discord import app_commands
from discord.ext import commands
import const

class Persona_update(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
        
    @app_commands.command(name='persona', description='チャットボットが保有しているペルソナをアップデートします')
    async def persona_update(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        # 1. チャット履歴の取得
        try:
            history_text = await self._fetch_history_text(interaction)
        except Exception as e:
            await interaction.followup.send(f"❌ 履歴取得中にエラー: {e}")
            return
        
        test_file = "output.txt"
        
        with open(test_file, mode='w', encoding='utf-8') as f:
            f.write(history_text)
            
        print('テストエンド')
        
    async def _fetch_history_text(self, interaction: discord.Interaction):
        """チャンネルから履歴を取得してテキスト化するヘルパーメソッド"""
        channel = self.bot.get_channel(const.CHAT_CHANNEL_ID)
        if not channel:
            try:
                channel = await self.bot.fetch_channel(const.CHAT_CHANNEL_ID)
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

        output_text = ""
        for msg in reversed(messages):
            date_japan = msg.created_at.astimezone().strftime('%Y-%m-%d %H:%M')
            output_text += f"[{date_japan}] {msg.author.display_name}: {msg.content}\n"
        
        return output_text