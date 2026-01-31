# cogs/utility.py
import discord
import const
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
        
    @app_commands.command(name="join_voicechannel", description="botをボイスチャンネルに参加させます。")
    async def join_voicechannel(self, interaction: discord.Interaction):
        self.logger.info("ボイスチャンネルへのbotの参加を待機中")
        
        # 参加するボイスチャンネルのID指定
        channel_id = const.YOMIAGE_YOMI_CHANNEL_ID
        
        # 2. IDからチャンネルオブジェクトを取得
        channel = interaction.guild.get_channel(channel_id)

        # チャンネルが見つからない、またはボイスチャンネルでない場合のガード
        if channel is None or not isinstance(channel, discord.VoiceChannel):
            await interaction.response.send_message("指定されたボイスチャンネルが見つかりませんでした。", ephemeral=True)
            return

        # 3.すでにBotがほかのチャンネルにいる場合のハンドリング
        voice_client = interaction.guild.voice_client
        
        try:
            if voice_client is not None:
                # すでに接続済みの場合は移動する
                await voice_client.move_to(channel)
                message = f"{channel.name} に移動しました。"
            else:
                # 新規接続
                await channel.connect()
                message = f"{channel.name} に参加しました。"
            
            # 4. ユーザーへの応答（これがないと「インタラクションに失敗しました」と出る）
            await interaction.response.send_message(message)

        except Exception as e:
            self.logger.error(f"接続エラー: {e}")
            await interaction.response.send_message("接続中にエラーが発生しました。", ephemeral=True)
        
    @app_commands.command(name="leave_voicechannel", description="botをボイスチャンネルから退出させます。")
    async def leave_voicechannel(self, interaction: discord.Interaction):
        self.logger.info("ボイスチャンネルからの切断リクエストを受信")

        # サーバー内のBotのボイス接続状況を取得
        voice_client = interaction.guild.voice_client

        if voice_client is not None and voice_client.is_connected():
            try:
                # 読み上げ中であれば停止させる（エラー防止）
                if voice_client.is_playing():
                    voice_client.stop()

                # 切断処理
                await voice_client.disconnect()
                await interaction.response.send_message("ボイスチャンネルから退出しました。")
                self.logger.info("切断完了")

            except Exception as e:
                self.logger.error(f"切断エラー: {e}")
                await interaction.response.send_message("切断中にエラーが発生しました。", ephemeral=True)
        else:
            # そもそも接続していない場合
            await interaction.response.send_message("Botはボイスチャンネルに参加していません。", ephemeral=True)
            
async def setup(bot):
    await bot.add_cog(Utility(bot))