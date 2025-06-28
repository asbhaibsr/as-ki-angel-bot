import os

# --- Bot Configuration ---
BOT_TOKEN = os.getenv('7467073514:AAFQ3vCZXTdee9McGkgvgZky70GsDjahcAA')
API_ID = int(os.getenv('API_ID', '29970536')) # Default value for development, but should be set in .env
API_HASH = os.getenv('API_HASH', 'f4bfdcdd4a5c1b7328a7e4f25f024a09') # Default value for development, but should be set in .env

# --- Database Configuration ---
MONGO_URI = os.getenv('MONGO_URI')

# --- Channel and Group Configuration ---
MANDATORY_CHANNEL_USERNAME = os.getenv('MANDATORY_CHANNEL_USERNAME', 'asbhai_bsr')
MANDATORY_CHANNEL_LINK = f"https://t.me/{MANDATORY_CHANNEL_USERNAME}"
OFFICIAL_GROUP_LINK = os.getenv('OFFICIAL_GROUP_LINK', 'https://t.me/asbhai_bsr')
ISTREAMX_LINK = os.getenv('ISTREAMX_LINK', 'https://t.me/istreamx')
ASPREMIUMAPPS_LINK = os.getenv('ASPREMIUMAPPS_LINK', 'https://t.me/aspremiumapps')

# --- Bot Owner Configuration ---
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', '6045817909'))  # Set your actual user ID here

# --- Learning Configuration ---
MAX_LEARNING_MEMORY = 1000
MIN_WORD_LENGTH = 2
MAX_WORD_LENGTH = 5
LEARNING_COOLDOWN = 0.5  # seconds between learning from same user

# --- Premium Configuration ---
PREMIUM_PRICE = "500 Rs."
PREMIUM_DURATION_MONTHS = 5
UPI_ID = "arsadsaifi8272@ibl"

# --- Response Configuration ---
STICKER_PROBABILITY = 0.3  # 30% chance to respond with sticker
RESPONSE_PROBABILITY = 0.8  # 80% chance to respond to messages
FAST_MODE = True  # Enable fast response mode

# Validation
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set.")

if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable not set.")

if not BOT_OWNER_ID or BOT_OWNER_ID == 0:
    print("WARNING: BOT_OWNER_ID is not set. Owner commands will not work.")
    print(f"Current BOT_OWNER_ID value: {BOT_OWNER_ID}")
    print("Set your user ID as BOT_OWNER_ID environment variable.")
