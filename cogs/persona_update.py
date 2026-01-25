import discord
import os
import asyncio
from discord import app_commands
from discord.ext import commands
from datetime import timezone, timedelta
from utils.send_mail import SakuraMailSender
import const

# JST定義
JST = timezone(timedelta(hours=9))

class Persona_update(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
        self.persona_file = '.persona'
        self.mail_sender = SakuraMailSender(logger=self.logger)
        
        # ここにあった self.scheduled_task.start() は削除します

    # スラッシュコマンド
    @app_commands.command(name='persona', description='チャットボットが保有しているペルソナをアップデートします')
    async def persona_update(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            channel = self.bot.get_channel(const.CHAT_CHANNEL_ID)
            if not channel:
                try:
                    channel = await self.bot.fetch_channel(const.CHAT_CHANNEL_ID)
                except Exception as e:
                    self.logger.error(f"Scheduler: チャットボットチャンネル取得失敗: {e}")
                    return

            # 共通ロジックを呼び出す
            result_msg = await self.execute_update_logic(channel)
            await interaction.followup.send(f'✅ {result_msg}')
        except Exception as e:
            await interaction.followup.send(f"❌ エラーが発生しました: {e}")

    # ==================================================================
    # 外部(Scheduler)から呼び出せる共通ロジック (publicメソッド化)
    # ==================================================================

    async def execute_update_logic(self, channel: discord.TextChannel) -> str:
        """
        ペルソナ更新の実処理。
        成功時はメッセージを返し、失敗時はExceptionを発生させる。
        """
        # 1. チャット履歴の取得
        history_text = await self._fetch_history_text(channel)
        if history_text is None:
            raise Exception("履歴が取得できませんでした")

        # 2. ファイル読み込み
        now_persona = ""
        if os.path.exists(self.persona_file):
            try:
                with open(self.persona_file, mode='r', encoding='utf-8') as f:
                    now_persona = f.read()
            except Exception as e:
                self.logger.error(f"ペルソナファイル読み込みエラー: {e}")
                now_persona = "（読み込み失敗）"
        else:
            now_persona = "（新規作成）"

        # 3. プロンプト合成
        prompt = f'''
以下はとあるチャットルームでの直近の会話履歴です。
{history_text}
また現在把握しているペルソナは以下のとおりです。
{now_persona}
現在このチャットルームにいる全員のペルソナ更新してまとめ直してください。
また好きなことや嫌いなことなど、以降あなたがあぴとしてチャットをしていくうえで記憶しておくといいことをまとめておいてください。
このペルソナは総文字数は最大2000~2500文字の範囲に抑え、単純増加ではなく増えすぎる場合には要約して短縮し、文字数の超過と大幅な減少にはペナルティを与えます。
なおこのチャットの返答は、チャットボットへ学習させるためのペルソナとして活用するため、前置きや装飾は不要です。
'''
        try:
            with open('.test', mode='w', encoding='utf-8') as f:
                f.write(prompt)
            # ログに残しておくと確認しやすいです（不要なら削除可）
            self.logger.info("Prompt content saved to .test successfully.")
        except Exception as e:
            self.logger.error(f"プロンプト保存エラー (.test): {e}")     
        
        # 4. API送信
        new_persona_content = await self._call_api_mock(prompt)

        # 5. 新ペルソナメール送信
        subject = 'チャットボットのペルソナが更新されました'
        
        try:
            self.mail_sender.send(subject, new_persona_content)
            self.logger.info("メール送信成功")
        except Exception as e:
            self.logger.error(f'メール送信失敗：{e}')

        # 5. ファイル保存
        with open(self.persona_file, mode='w', encoding='utf-8') as f:
            f.write(new_persona_content)
            
        self.logger.info(f"Persona updated successfully. Length: {len(new_persona_content)}")
        return "ペルソナを更新しました！"

    # --- ヘルパー関数群 ---
    async def _call_api_mock(self, prompt: str) -> str:
        # (前回のまま変更なし)
        await asyncio.sleep(2)
        response = await self.bot.ai_throw_gemini.generate_response(prompt)
        return response

    async def _fetch_history_text(self, channel):
        # (前回のまま変更なし)
        if not channel: return None
        messages = []
        try:
            async for msg in channel.history(limit=100):
                messages.append(msg)
        except Exception as e:
            self.logger.error(f"履歴取得権限エラー: {e}")
            raise e
        
        if not messages: return None

        output_text = ""
        for msg in reversed(messages):
            created_at = msg.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            date_japan = created_at.astimezone(JST).strftime('%Y-%m-%d %H:%M')
            output_text += f"[{date_japan}] {msg.author.display_name}: {msg.content}\n"
        
        return output_text

async def setup(bot):
    await bot.add_cog(Persona_update(bot))