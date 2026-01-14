import os
from bot import BotApp

class Main:
    def __init__(self):
        print("Main class initialized")
        
    def run(self):
        print("Running the main application")
        print("Attempting to get Discord API key...")
        try:
            self.discord_api_key = os.getenv("DISCORD_BOT_TOKEN2")
            if not self.discord_api_key:
                raise ValueError("DISCORD_BOT_TOKEN2 environment variable is not set")
        except Exception as e:
            print(f"Error getting API key: {e}")
            return
        
        print(f"Discord API key obtained: {self.discord_api_key[:4]}****")
        
        botapp = BotApp()
        botapp.start(self.discord_api_key)

if __name__ == "__main__":
    main_instance = Main()
    main_instance.run()
    