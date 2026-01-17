# cogs/finance.py
import discord
import io
from discord import app_commands
from discord.ext import commands
import const  # 作成したconst.pyをインポート

class Finance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger

    @app_commands.command(name="pay_history", description="支払い履歴を表示します")
    async def pay_history(self, interaction: discord.Interaction):
        self.logger.info("支払い履歴コマンド実行中...")
        await interaction.response.defer()

        # 1. 履歴データの取得
        try:
            history_text = await self._fetch_history_text(interaction)
            if not history_text:
                return 
        except Exception as e:
            await interaction.followup.send(f"❌ 履歴取得中にエラー: {e}")
            return

        # 2. AIによる解析とコメント生成
        try:
            # 抽出
            extract_prompt = const.PROMPT_EXTRACT_PAYMENT.format(history_text=history_text)
            self.logger.info('支出データを解析しています...')
            # bot本体に持たせているAIインスタンスを利用
            pay_data = await self.bot.ai_throw_gemma27.generate_response(extract_prompt)

            # コメント生成
            comment_prompt = const.PROMPT_GENERATE_COMMENT.format(
                pay_data=pay_data, 
                user_name=interaction.user.display_name
            )
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
        channel = self.bot.get_channel(const.PAY_HISTORY_CHANNEL_ID)
        if not channel:
            try:
                channel = await self.bot.fetch_channel(const.PAY_HISTORY_CHANNEL_ID)
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

async def setup(bot):
    await bot.add_cog(Finance(bot))