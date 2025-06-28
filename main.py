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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

class AskiAngelBot(Client):
    def __init__(self):
        super().__init__(
            "aski_angel_bot", # Session name
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            parse_mode=ParseMode.MARKDOWN # Default parse mode
        )
        self.db = db
        self.utils = BotUtils(self) # Pass self (the Pyrogram client) to utils
        self.is_connected = False # To track connection status
        print("Bot initialized. Connecting to Telegram...")

    async def start(self):
        await super().start()
        self.is_connected = True
        self.me = await self.get_me() # Get bot's own info
        print(f"Bot @{self.me.username} started!")
        
        # Register handlers
        self.register_handlers()

        # Start keep-alive ping in background
        asyncio.create_task(self.start_ping_self())

    async def stop(self):
        await super().stop()
        self.is_connected = False
        print("Bot stopped.")

    async def start_ping_self(self):
        # Run the synchronous ping_self in a separate thread/executor
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, ping_self)

    def register_handlers(self):
        # Register handlers from imported modules
        admin.register_admin_handlers(self, self.utils)
        learning.register_learning_handlers(self, self.utils)
        premium.register_premium_handlers(self, self.utils)
        start.register_start_handlers(self, self.utils)
        print("All handlers registered!")

if __name__ == "__main__":
    # Start the Flask keep-alive server in a separate thread
    keep_alive()
    
    # Initialize and run the bot
    bot = AskiAngelBot()
    
    try:
        # Use run_until_complete for synchronous execution of async main
        asyncio.get_event_loop().run_until_complete(bot.start())
        # This will keep the bot running until it's stopped manually or by an error
        asyncio.get_event_loop().run_forever() 
    except KeyboardInterrupt:
        print("Bot stopped by KeyboardInterrupt.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if bot.is_connected:
            asyncio.get_event_loop().run_until_complete(bot.stop())
        db.client.close() # Close MongoDB connection
        print("MongoDB connection closed.")
