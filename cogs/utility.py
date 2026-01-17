# cogs/utility.py
import discord
from discord import app_commands
from discord.ext import commands
from tools.ip_checker import IpChecker

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger

    @app_commands.command(name="ping", description="Botの応答速度を表示します")
    async def ping(self, interaction: discord.Interaction):
        latency_ms = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"🏓 Pong! ({latency_ms}ms)")

    @app_commands.command(name="ip_checker", description="IPアドレスを確認します")
    async def ip_checker(self, interaction: discord.Interaction):
        self.logger.info("IPアドレス確認コマンド実行中...")
        await interaction.response.defer()
        
        checker = IpChecker(logger=self.logger)
        ip_address = await checker.check_ip()
        
        await interaction.followup.send(ip_address)

async def setup(bot):
    await bot.add_cog(Utility(bot))