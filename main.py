import os
import asyncio
import logging
from pyrogram import Client
from pyrogram.enums import ParseMode

from config import API_ID, API_HASH, BOT_TOKEN, MONGO_URI, BOT_OWNER_ID, MANDATORY_CHANNEL_USERNAME
from database import db
from keep_alive import keep_alive, ping_self
from utils import BotUtils

# --- Import Handlers ---
from handlers import admin, learning, premium, start

# --- environment variables ---
STRING_SESSION = os.getenv('STRING_SESSION') # यह लाइन पहले से ही सही है

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

class AskiAngelBot(Client):
    def __init__(self):
        # यहाँ बदलाव है
        super().__init__(
            "AskiAngelBotSession",  # <-- यहाँ एक छोटा, स्थिर सेशन नाम दें
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN if not STRING_SESSION else None,
            parse_mode=ParseMode.MARKDOWN,
            session_string=STRING_SESSION # <-- STRING_SESSION को यहाँ पास करें
        )
        self.db = db
        self.utils = BotUtils(self)
        self.is_connected = False
        print("Bot initialized. Connecting to Telegram...")

    async def start(self):
        await super().start()
        self.is_connected = True
        self.me = await self.get_me()
        print(f"Bot @{self.me.username} started!")

        self.register_handlers()
        asyncio.create_task(self.start_ping_self())

    async def stop(self):
        await super().stop()
        self.is_connected = False
        print("Bot stopped.")

    async def start_ping_self(self):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, ping_self)

    def register_handlers(self):
        admin.register_admin_handlers(self, self.utils)
        learning.register_learning_handlers(self, self.utils)
        premium.register_premium_handlers(self, self.utils)
        start.register_start_handlers(self, self.utils)
        print("All handlers registered!")

if __name__ == "__main__":
    keep_alive()

    bot = AskiAngelBot()

    try:
        asyncio.get_event_loop().run_until_complete(bot.start())
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print("Bot stopped by KeyboardInterrupt.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if bot.is_connected:
            asyncio.get_event_loop().run_until_complete(bot.stop())
        db.client.close()
        print("MongoDB connection closed.")
