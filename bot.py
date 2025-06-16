from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN

class Bot(Client):
    def __init__(self):
        super().__init__(
            "save_restricted_bot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="plugins"),
            workers=50,
            sleep_threshold=30,  # For large file downloads
            timeout=60  # Increased for stability
        )

    async def start(self):
        await super().start()
        print("Bot Started")

    async def stop(self, *args):
        await super().stop()
        print("Bot Stopped")

Bot().run()
