import google.genai as genai
from google.genai import types

class GemmaChatbot:
    def __init__(self, api_key: str, model_name: str = "gemma-3-27b-it"):
        """
        初期化メソッド
        Args:
            api_key (str): Google Gemini API Key
            model_name (str): 使用するモデル名
        """
        print(f'GemmaChatbot initialized (Model: {model_name})')
        
        self.model_name = model_name
        
        # クライアントの初期化
        self.client = genai.Client(api_key=api_key)

        # 安全設定（制限解除）
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

    async def generate_response(self, user_input: str) -> str:
        """
        プロンプトを生成してAPIに送信するメソッド
        """
        print('throw gemma')
        print(f'user model ({self.model_name}) processing input.')
        try:
            user_prompt = user_input

            # APIリクエスト (非同期)
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    safety_settings=self.safety_settings
                )
            )
            
            return response.text

        except Exception as e:
            error_msg = f"Google Gen AI API Error: {e}"
            print(error_msg)
            return "申し訳ありません。エラーが発生しました。"