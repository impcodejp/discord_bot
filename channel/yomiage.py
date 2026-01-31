import const

class YOMIAGE:
    def __init__(self, logger = None):
        logger.info('yomiage initialize')
        self.logger = logger
        self.yomi_channel_id = const.YOMIAGE_YOMI_CHANNEL_ID
        self.logger.info('読み上げチャンネルシステムのinitialize完了')
        
    async def process(self, message):
        self.yomi_channel = self.bot.get_channel(self.yomi_channel_id)
        if not self.yomi_channel:
            try:
                self.yomi_channel = await self.bot.fetch_channel(self.yomi_channel_id)
            except Exception as e:
                self.logger.error(f'チャンネルが見つかりません。：{self.yomi_channel_id}:{e}')

            