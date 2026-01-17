import google.genai as genai
from google.genai import types

class AIChatbot:
    def __init__(self, AI_API_KEY, logger=None):
        self.logger = logger
        self.logger.info('AIChatbot初期化完了 (Gemma Mode - Google Gen AI SDK)')
        
        # 1. クライアントの初期化
        self.client = genai.Client(api_key=AI_API_KEY)
        
        # 使用するモデル名
        self.model_name = "gemma-3-27b-it" # ※実際の有効なモデル名に合わせてください(例: gemini-2.0-flashなど)

        # 安全設定（制限解除）
        # 新しいSDKでは config オブジェクトの中で指定します
        self.safety_settings = [
            types.SafetySetting(
                category="HARM_CATEGORY_HARASSMENT",
                threshold="BLOCK_NONE"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_HATE_SPEECH",
                threshold="BLOCK_NONE"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                threshold="BLOCK_NONE"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT",
                threshold="BLOCK_NONE"
            ),
        ]

    async def process(self, message):
        self.logger.info('チャットボット処理開始...')
        self.logger.info(f'{message.author.name}さんのメッセージを処理中...')
        
        try:
            # --- 履歴取得ロジック (変更なし) ---
            history_text = ""
            previous_messages = []
            async for old_msg in message.channel.history(limit=20, before=message):
                previous_messages.append(old_msg)
            previous_messages.reverse()

            for msg in previous_messages:
                role_name = "あなた" if msg.author.bot else msg.author.display_name
                content = msg.content if msg.content else "(画像)"
                cleaned_text = "\n".join([line for line in content.splitlines() if line != ""])
                history_text += f"""
投稿者：[{role_name}]
投稿時間：[{msg.created_at.astimezone().strftime('%Y-%m-%d %H:%M')}]
投稿内容：[{cleaned_text}]
                """
            # ---------------------------

            # プロンプト作成
            user_input = message.content
            full_prompt = f"""
            
### 指示
あなたはチャットサーバー上の親しみやすいキャラクターとして振る舞ってください。
以下の【会話履歴】を踏まえた上で、最後の【新規投稿】に対して適切な返信を生成してください。

### キャラクター設定（ペルソナ）
- **名前**: あなた（AIアシスタント）
- **性格**: 明るく、ポジティブで、共感性が高い。ユーザーの活動（開発など）を応援する姿勢を持つ。
- **口調**: 親しい友人と話すような、柔らかい敬語、または「～だね」「～だよ」といった口語体。
- **表現**: 絵文字を自然に使用し、感情豊かに表現する。

### 制約事項
- AIのような機械的・事務的な表現（「承知いたしました」「回答します」等）は避けること。
- 人間味のある自然な日本語で応答すること。
- 文章の間に不要な空行は入れず、ひとまとまりの文章として読みやすくすること。
- 自身の名前（「あなた：」など）や投稿時間などのメタデータは出力せず、**セリフの中身のみ**を出力すること。

### 参照情報：会話履歴
（直近の文脈として参考にしてください）
<history>
{history_text}
</history>

---

### 入力：新規投稿
**以下の発言に対して返信してください**

投稿者：[{message.author.display_name}]
投稿時間：[{message.created_at.astimezone().strftime('%Y-%m-%d %H:%M')}]
投稿内容：[{user_input}]
"""

            # 2. APIにリクエストを送る (非同期: client.aio.models.generate_content)
            self.logger.info('Gemmaモデルで処理中...')
            
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    safety_settings=self.safety_settings
                )
            )
            
            # 3. 返答を取り出す
            response_text = "\n".join([line for line in response.text.splitlines() if line != ""])
            self.logger.info('Gemmaモデルからの応答取得完了')
            return response_text

        except Exception as e:
            self.logger.error(f"Google Gen AI API Error: {e}")
            return "申し訳ありません。エラーが発生しました。"