import re
import random
import time
import asyncio # Added for async compatibility
from config import BOT_OWNER_ID, MIN_WORD_LENGTH, MAX_WORD_LENGTH, LEARNING_COOLDOWN # Added MIN/MAX_WORD_LENGTH from config

class BotUtils:
    def __init__(self, app):
        self.app = app
        self.user_cooldowns = {}  # Track user message cooldowns

    async def check_member_status(self, user_id, channel_username):
        """Checks if a user is a member of the mandatory channel."""
        try:
            member = await self.app.get_chat_member(f"@{channel_username}", user_id)
            return member.status in ['member', 'administrator', 'creator']
        except Exception as e:
            # If we can't check membership due to admin privileges, skip verification
            if "CHAT_ADMIN_REQUIRED" in str(e) or "USER_NOT_PARTICIPANT" in str(e): # Added USER_NOT_PARTICIPANT
                print(f"Cannot check membership for {user_id} in @{channel_username}: Bot needs admin rights/user not found - skipping verification")
                return True  # Allow user to proceed since we can't verify
            print(f"Error checking channel membership for {user_id}: {e}")
            return False

    def is_owner(self, user_id):
        """Checks if user is the bot owner."""
        return user_id == BOT_OWNER_ID

    def is_admin_command(self, message):
        """Checks if message contains admin commands."""
        admin_commands = ['/admin', '/settings', '/stats', '/broadcast', '/addpremium', '/removepremium', '/listpremium', '/premiumstats', '/logs']
        return message.text and any(message.text.startswith(cmd) for cmd in admin_commands)

    async def is_premium_user(self, user_id):
        """Check if user has active premium subscription."""
        from database import db # Local import to avoid circular dependency
        
        if user_id == BOT_OWNER_ID:
            return True
            
        return await db.is_premium(user_id) # Use the async method from db

    def format_time_remaining(self, timestamp):
        """Formats remaining time from timestamp."""
        remaining = timestamp - time.time()
        if remaining <= 0:
            return "Expired"

        days = int(remaining // (24 * 3600))
        hours = int((remaining % (24 * 3600)) // 3600)
        minutes = int((remaining % 3600) // 60)

        if days > 0:
            return f"{days} days, {hours} hours"
        elif hours > 0:
            return f"{hours} hours, {minutes} minutes"
        else:
            return f"{minutes} minutes" if minutes > 0 else "Less than a minute"

    def extract_short_response(self, text):
        """Extracts 1-5 word responses from text."""
        if not text:
            return None

        # Clean the text
        text = re.sub(r'[^\w\s\u0900-\u097F]', '', text)  # Keep Hindi and English chars
        words = text.split()

        if len(words) <= MAX_WORD_LENGTH: # Use config for max length
            return text

        # Try to find meaningful short phrases
        patterns = [
            r'\b(हाँ|नहीं|अच्छा|बुरा|सही|गलत|ठीक|वाह|अरे)\b',
            r'\b(yes|no|good|bad|ok|wow|hey|nice|cool)\b',
            r'\b(👍|👎|😊|😢|😂|🤣|❤️|💯)\b'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Return up to 3 random matches, join them
                return ' '.join(random.sample(matches, min(len(matches), 3)))

        # Fallback: Return a random slice of 1-3 words
        start_index = random.randint(0, max(0, len(words) - 3))
        end_index = start_index + random.randint(1, min(3, len(words) - start_index))
        return ' '.join(words[start_index:end_index])

    def should_respond(self, message): # Removed group_data, not needed for this check
        """Determines if bot should respond to a message."""
        # Don't respond to commands
        if message.text and message.text.startswith('/'):
            return False

        # Don't respond to messages from bots
        if message.from_user and message.from_user.is_bot:
            return False

        # Don't respond too frequently to same user
        user_id = message.from_user.id if message.from_user else None
        current_time = time.time()

        if user_id and user_id in self.user_cooldowns:
            if current_time - self.user_cooldowns[user_id] < LEARNING_COOLDOWN: # Use config for cooldown
                return False

        if user_id:
            self.user_cooldowns[user_id] = current_time

        # Higher chance if message mentions bot or contains keywords
        text = message.text.lower() if message.text else ""
        
        # Check for bot mention or reply
        if message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.is_self:
            return random.random() < 0.95 # Very high chance if directly replied to bot

        bot_username = self.app.me.username.lower() if self.app.me else "askiangel" # Fallback if bot.me is not ready
        trigger_words = ['angel', 'bot', 'हाय', 'hello', 'hi', 'aski', bot_username]

        if any(word in text for word in trigger_words):
            return random.random() < 0.9  # 90% chance for direct mentions/keywords

        # Regular response probability
        from config import RESPONSE_PROBABILITY
        return random.random() < RESPONSE_PROBABILITY # Use config for general response probability

    def clean_text_for_learning(self, text):
        """Cleans text for learning purposes."""
        if not text:
            return None

        # Remove URLs, mentions, hashtags, and special characters
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'#\w+', '', text)
        
        # Keep only alphanumeric characters, spaces, and Hindi characters
        # Ensure it handles common punctuation by replacing them with spaces first, then cleaning
        text = re.sub(r'[.,!?;:()\'"]', ' ', text) # Replace common punctuation with space
        text = re.sub(r'[^\w\s\u0900-\u097F]', '', text) # Remove any remaining non-alphanumeric, non-space, non-hindi
        
        # Remove extra whitespace
        text = ' '.join(text.split()).strip()

        return text if len(text.split()) >= MIN_WORD_LENGTH else None # Use config for min word length
