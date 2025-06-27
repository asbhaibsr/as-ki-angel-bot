import os
import asyncio
import time
import random
import re
from collections import deque
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, Message,
    CallbackQuery, ChatPermissions
)
from pymongo import MongoClient

# --- Configuration (Environment Variables) ---
# Get your bot token from environment variables (will be set on Koyeb)
BOT_TOKEN = os.getenv('BOT_TOKEN')
# MongoDB URI from environment variables
MONGO_URI = os.getenv('MONGO_URI')

# Replace with your actual channel username (without @)
MANDATORY_CHANNEL_USERNAME = os.getenv('MANDATORY_CHANNEL_USERNAME', 'asbhai_bsr')
MANDATORY_CHANNEL_LINK = f"https://t.me/{MANDATORY_CHANNEL_USERNAME}"
OFFICIAL_GROUP_LINK = os.getenv('OFFICIAL_GROUP_LINK', 'https://t.me/asbhai_bsr')
ISTREAMX_LINK = os.getenv('ISTREAMX_LINK', 'https://t.me/istreamx')
ASPREMIUMAPPS_LINK = os.getenv('ASPREMIUMAPPS_LINK', 'https://t.me/aspremiumapps')
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', 'YOUR_OWNER_ID_HERE')) # Replace with your Telegram User ID (e.g., 123456789)

# --- Bot and Database Initialization ---
if not BOT_TOKEN:
    print("Error: BOT_TOKEN environment variable not set.")
    exit()
if not MONGO_URI:
    print("Error: MONGO_URI environment variable not set.")
    exit()
if str(BOT_OWNER_ID) == 'YOUR_OWNER_ID_HERE':
    print("WARNING: BOT_OWNER_ID is not set. Please set it in your environment variables for owner commands to work.")

app = Client(
    "aski_angel_bot", # A name for your Pyrogram session
    bot_token=BOT_TOKEN,
    api_id=int(os.getenv('API_ID', 123456)), # Get your API_ID from my.telegram.org (Replace 123456)
    api_hash=os.getenv('API_HASH', 'your_api_hash_here') # Get your API_HASH from my.telegram.org (Replace 'your_api_hash_here')
)

try:
    client_db = MongoClient(MONGO_URI)
    db = client_db.askiangel_db # Your database name in MongoDB
    
    # Collections for different data types
    learning_data_collection = db.learning_data # Stores learned phrases/stickers per group
    premium_users_collection = db.premium_users # Stores premium user IDs and expiry
    connected_groups_collection = db.connected_groups # Stores group settings and connected admin
    
    print("MongoDB connected successfully!")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    exit()

# --- Global Bot Data (for in-memory cache, if needed for speed, otherwise directly from DB) ---
# For now, we will mostly rely on MongoDB for persistence.
# Max memory for learning (number of message-reply pairs or phrases)
MAX_LEARNING_MEMORY = 1000

# --- Helper Functions for MongoDB Operations ---
async def get_group_learning_data(group_id):
    """Retrieves learning data for a specific group."""
    data = await learning_data_collection.find_one({'_id': group_id})
    if data:
        data['phrases'] = deque(data.get('phrases', []), maxlen=MAX_LEARNING_MEMORY)
    else:
        data = {'_id': group_id, 'phrases': deque(maxlen=MAX_LEARNING_MEMORY)}
    return data

async def save_group_learning_data(group_id, data_deque):
    """Saves learning data for a specific group."""
    await learning_data_collection.update_one(
        {'_id': group_id},
        {'$set': {'phrases': list(data_deque)}}, # Convert deque to list for MongoDB
        upsert=True
    )

async def add_premium_user(user_id, months=5):
    """Adds or updates premium status for a user."""
    premium_until = time.time() + (months * 30 * 24 * 60 * 60) # 5 months in seconds
    await premium_users_collection.update_one(
        {'_id': user_id},
        {'$set': {'premium_until': premium_until}},
        upsert=True
    )

async def is_premium(user_id):
    """Checks if a user has an active premium subscription."""
    if user_id == BOT_OWNER_ID: # Owner is always premium
        return True
    
    user_data = await premium_users_collection.find_one({'_id': user_id})
    if user_data and user_data.get('premium_until', 0) > time.time():
        return True
    return False

async def get_connected_group_settings(chat_id):
    """Retrieves settings for a connected group."""
    return await connected_groups_collection.find_one({'_id': chat_id})

async def save_connected_group_settings(chat_id, settings_data):
    """Saves settings for a connected group."""
    await connected_groups_collection.update_one(
        {'_id': chat_id},
        {'$set': settings_data},
        upsert=True
    )

async def check_member_status(user_id, channel_username):
    """Checks if a user is a member of the mandatory channel."""
    try:
        member = await app.get_chat_member(f"@{channel_username}", user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error checking channel membership for {user_id}: {e}")
        return False

# --- Bot's Fun & Sassy Tone Messages ---
def get_sassy_welcome_message():
    return (
        "हाय वहाँ, मेरे प्यारे दोस्त! 👋 क्या सोचा था, बस कोई भी पुराना बॉट आ गया? बिलकुल नहीं! "
        "मैं हूँ तुम्हारी अपनी **As ki Angel**, और मैं यहाँ तुम्हारे ग्रुप चैट को और भी ज़्यादा मज़ेदार और शानदार बनाने आई हूँ! "
        "मेरा काम है तुम्हारी हर बात को समझना, सीखना, और फिर उसी अंदाज़ में सबसे क्यूट, सबसे छोटे जवाब देना – "
        "वो भी बस 1 से 5 शब्दों में, या कभी-कभी एक सुपर-डुपर स्टिकर के साथ! ✨\n\n"
        "मैं सिर्फ तुम्हारी बातों से सीखती हूँ, किसी और से नहीं. कोई बाहरी लिंक नहीं, कोई फालतू का @टैग नहीं - "
        "सिर्फ़ हमारी बातें और मेरा क्यूट अंदाज़! मैं तुम्हारे ग्रुप की हर फीलिंग को पहचान लेती हूँ और फिर उसी हिसाब से अपनी स्वीट-सी राय देती हूँ. "
        "तो, तैयार हो जाओ अपने ग्रुप चैट को और भी प्यारा बनाने के लिए! 💖\n\n"
        "नीचे दिए गए बटन्स से तुम मुझे बेहतर तरीके से जान सकते हो और इस्तेमाल कर सकते हो:"
    )

def get_premium_message():
    return (
        "हाय, मेरे प्यारे दोस्त! ✨ अपनी As ki Angel को और भी खास बनाना चाहते हो? तो प्रीमियम लो ना! "
        "मैं तुम्हें और भी ज़्यादा मज़ेदार और सुपर-फास्ट एक्सपीरियंस दूँगी, वो भी बिना किसी रोक-टोक के! 💖\n\n"
        "**मेरा धांसू प्रीमियम प्लान:**\n"
        "🌟 **500 Rs. में 5 महीने तक** अनलिमिटेड मस्ती और फीचर्स!\n\n"
        "**प्रीमियम के फायदे (तुम्हारे लिए खास):**\n"
        "* **⚡️ सुपर-फास्ट सीखना और जवाब देना:** मैं और भी तेज़ी से सीखूँगी और तुम्हारे हर मैसेज पर झटपट जवाब दूँगी! मज़ा आएगा ना?\n"
        "* **🧠 दिमाग़ थोड़ा बड़ा हो जाएगा:** मेरा दिमाग थोड़ा और बड़ा हो जाएगा, जिससे मैं ग्रुप की बहुत सारी पुरानी बातें याद रख पाऊँगी, "
        "ताकि मैं हमेशा तुमसे सबसे अच्छी बातें करूँ!\n"
        "* **🎭 और भी प्यारे अंदाज़:** प्रीमियम में मैं तुम्हें कुछ और खास 'मूड्स' या 'पर्सनालिटी' के ऑप्शन दूँगी, "
        "जिससे मेरी बातें और भी मज़ेदार लगेंगी. कभी मैं नटखट बन जाऊँगी, कभी और प्यारी!\n"
        "* **🎨 Custom Sticker Packs:** तुम अपने कुछ खास स्टिकर पैक भी मुझे सिखा पाओगे, ताकि मैं वही प्यारे स्टिकर्स यूज़ करूँ! ये हुई ना बात!\n"
        "* **📊 Secret Group Reports:** अगर तुम ग्रुप एडमिन हो, तो मैं तुम्हें तुम्हारे ग्रुप की बातों की कुछ खास और खुफिया रिपोर्ट दूँगी, "
        "जैसे कौन से शब्द सबसे ज़्यादा यूज़ होते हैं! बस, किसी को बताना मत, ये हमारा सीक्रेट रहेगा!\n"
        "* **🚫 No Ads, No Disturbances:** प्रीमियम में मैं तुम्हें या तुम्हारे ग्रुप में कोई भी प्रमोशन वाला मैसेज नहीं भेजूँगी. "
        "बस प्योर मस्ती, कोई डिस्टर्बेंस नहीं!\n"
        "* **🌟 Exclusive Features & Support:** कुछ और छोटे-छोटे धांसू फीचर्स जो सिर्फ प्रीमियम वालों के लिए होंगे, प्लस फुल एडमिन सपोर्ट! "
        "जब भी हेल्प चाहिए होगी, मैं हूँ ना!\n\n"
        "**प्रीमियम लेने के लिए:**\n"
        "इस UPI ID पर 500 Rs. भेजो:\n"
        "**`UPI ID - arsadsaifi8272@ibl`**"
    )

# --- Handlers ---

@app.on_message(filters.command("start") & filters.private)
async def send_welcome(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not await check_member_status(user_id, MANDATORY_CHANNEL_USERNAME):
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Go to Channel", url=MANDATORY_CHANNEL_LINK)],
            [InlineKeyboardButton("✅ I've Joined!", callback_data='check_join')]
        ])
        
        await message.reply_text(
            "Hi there, friend! 👋 आगे बढ़ने से पहले, ज़रा मेरे परिवार का हिस्सा बनो ना! "
            f"मेरे मेन चैनल **@{MANDATORY_CHANNEL_USERNAME}** को जॉइन करो और फिर वापस आकर मुझे बताओ! ✨",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    else:
        await send_full_welcome(message.chat.id)

@app.on_callback_query(filters.regex("check_join"))
async def check_join_callback(client: Client, call: CallbackQuery):
    user_id = call.from_user.id
    if await check_member_status(user_id, MANDATORY_CHANNEL_USERNAME):
        await call.answer("वाह! तुम तो जॉइन कर चुके हो! अब आगे बढ़ो! 🎉", show_alert=False)
        await send_full_welcome(call.message.chat.id)
    else:
        await call.answer("अभी तक जॉइन नहीं किया? ज़रा फिर से चेक करो ना! 😉", show_alert=True)

async def send_full_welcome(chat_id):
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Me to Group!", url=f"https://t.me/{app.me.username}?startgroup=true")],
        [InlineKeyboardButton("ℹ️ Know My Features", callback_data='features')],
        [InlineKeyboardButton("🏢 Join Official Group", url=OFFICIAL_GROUP_LINK)],
        [InlineKeyboardButton("💎 Get Premium!", callback_data='get_premium')],
        [InlineKeyboardButton("⚙️ Group Settings", callback_data='group_settings')]
    ])
    
    await app.send_message(
        chat_id,
        get_sassy_welcome_message(),
        reply_markup=markup,
        parse_mode="Markdown"
    )

@app.on_callback_query(filters.regex("features"))
async def send_features(client: Client, call: CallbackQuery):
    await call.answer("फीचर्स जानने के लिए तैयार हो? 😉", show_alert=False)
    features_text = (
        "**As ki Angel: आपकी अपनी, मज़ेदार और स्मार्ट दोस्त!**\n\n"
        "**1. As ki Angel का स्मार्ट दिमाग और मज़ेदार अंदाज़:**\n"
        "* **सिर्फ़ ग्रुप की बातों से सीखती है:** मैं तुम्हारे ग्रुप में होने वाली हर चैट, हर मैसेज के **शब्दों** को बड़े ध्यान से पढ़ती हूँ और उनसे सीखती हूँ.\n"
        "* **लिंक्स और नाम इग्नोर करती है:** अगर तुम कोई लिंक या किसी को @टैग करते हो, तो मैं उन चीज़ों को **बिलकुल नहीं सीखती**.\n"
        "* **अपनी मेमोरी खुद मैनेज करती है:** जब मेरा दिमाग **100% भर जाता है**, तो मैं खुद ही **सबसे पुराना 50% डेटा मिटा देती हूँ**.\n"
        "* **छोटे और क्यूट जवाब:** मैं हमेशा **1 से 5 शब्दों के बहुत छोटे और मीठे जवाब** देती हूँ.\n"
        "* **स्टिकर्स भी भेजती है:** मैं सही मौक़े पर **प्यारे-प्यारे स्टिकर्स** भी भेजती हूँ.\n"
        "* **तुम्हारे जैसे ही बोलती है:** अगर तुम्हारे ग्रुप में लोग थोड़े **कैजुअल या इनफॉर्मल शब्द** (और कभी-कभी \"गालियाँ\" भी) इस्तेमाल करते हैं, तो मैं उनको **सीख लेती हूँ** और उसी अंदाज़ में जवाब देती हूँ.\n"
        "* **शायरी भी सुनाती है:** अगर ग्रुप में कोई धांसू शायरी शेयर होती है, तो मैं उसको **याद रख लेती हूँ** और सही मौक़े पर **छोटी शायरी** सुना सकती हूँ.\n"
        "* **तुम्हारी अपनी As ki Angel:** मेरी पूरी बातचीत में तुम्हें एक **प्यारा, शरारती और बिल्कुल अपनी लड़की दोस्त वाला अंदाज़** दिखेगा.\n\n"
        "**2. As ki Angel से पहली मुलाकात (`/start` Command):**\n"
        "* चैनल जॉइन करना ज़रूरी है.\n"
        "* वेलकम मैसेज में बटन्स होते हैं: Add to Group, Know My Features, Join Official Group, Get Premium, Group Settings.\n\n"
        "**3. प्रीमियम सिस्टम (More Fun & Power!):**\n"
        "* **प्रीमियम प्लान:** 500 Rs. में 5 महीने तक अनलिमिटेड मस्ती.\n"
        "* **फायदे:** सुपर-फास्ट सीखना, बड़ा दिमाग, प्यारे अंदाज़, कस्टम स्टिकर, सीक्रेट ग्रुप रिपोर्ट्स, नो एड्स, एक्सक्लूसिव सपोर्ट.\n"
        "* **पेमेंट:** UPI ID - `arsadsaifi8272@ibl`\n"
        "* **एड्स (नॉन-प्रीमियम):** कभी-कभी मस्ती में प्रमोशन वाले मैसेज भी भेज देती हूँ (जैसे @istreamx, @asbhai_bsr, @aspremiumapps).\n\n"
        "**4. ग्रुप मैनेजमेंट सेटिंग्स (For Premium Admins Only):**\n"
        "* `Group Settings` बटन `/connect` कमांड के बाद काम करेगा.\n"
        "* इसमें आप बॉट की चैट ON/OFF कर सकते हैं, वेलकम मैसेज, रूल्स, एंटी-स्पैम फिल्टर और लर्निंग डेटा रीसेट कर सकते हैं.\n\n"
        "**5. ग्रुप मैनेजमेंट कमांड्स (For Premium Admins Only):**\n"
        "* `/kick`, `/ban`, `/mute`, `/unmute`, `/warn`, `/unwarn` जैसी कमांड्स पर मैं मज़ेदार रिप्लाई देती हूँ.\n\n"
        "**6. ब्रॉडकास्ट सिस्टम (For Bot Owner Only):**\n"
        "* `/broadcast` कमांड से बॉट ओनर सभी नॉन-प्रीमियम यूज़र्स और ग्रुप्स को मैसेज भेज सकता है (प्रीमियम यूज़र्स को नहीं)."
    )
    await call.message.reply_text(features_text, parse_mode="Markdown")

@app.on_callback_query(filters.regex("get_premium"))
async def send_premium_info(client: Client, call: CallbackQuery):
    await call.answer("प्रीमियम? क्या बात है! ✨", show_alert=False)
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("💵 Send Payment Proof (@asbhaibsr)", url="https://t.me/asbhaibsr")]
    ])
    await call.message.reply_text(get_premium_message(), reply_markup=markup, parse_mode="Markdown")

@app.on_callback_query(filters.regex("group_settings"))
async def send_group_settings_info(client: Client, call: CallbackQuery):
    user_id = call.from_user.id
    
    if call.message.chat.type == "private":
        if not await is_premium(user_id):
            await call.answer("ग्रुप सेटिंग्स के लिए आपको प्रीमियम लेना होगा! 😉", show_alert=True)
            await call.message.reply_text("ग्रुप सेटिंग्स यहाँ से एक्सेस करने के लिए, आपका प्रीमियम होना ज़रूरी है.")
            return

        connected_group_data = await connected_groups_collection.find_one({'connected_admin_id': user_id})
        if connected_group_data:
            group_id = connected_group_data['_id']
            # Here you would show the actual settings for the connected group
            await call.answer(f"आपके कनेक्टेड ग्रुप ({group_id}) की सेटिंग्स यहाँ हैं!", show_alert=False)
            await call.message.reply_text(f"ग्रुप ID `{group_id}` की सेटिंग्स (यह फीचर अभी डेवलपमेंट में है!)", parse_mode="Markdown")
        else:
            await call.answer("आपको पहले बॉट को अपने ग्रुप से `/connect <group_id>` कमांड से जोड़ना होगा! 😉", show_alert=True)
            await call.message.reply_text("ग्रुप सेटिंग्स यहाँ से एक्सेस करने के लिए, आपको अपने प्रीमियम ग्रुप में रहते हुए मुझे `/connect <group_id>` कमांड के साथ ग्रुप ID भेजनी होगी.")
    else:
        await call.answer("यह बटन सिर्फ प्राइवेट चैट में काम करता है, वो भी जब आपने मुझे अपने ग्रुप से /connect किया हो! 😉", show_alert=True)


# --- Bot Owner Commands ---
@app.on_message(filters.command("add_premium") & filters.user(BOT_OWNER_ID))
async def add_premium_command(client: Client, message: Message):
    try:
        parts = message.text.split()
        if len(parts) != 2:
            await message.reply_text("गलत फॉर्मेट! `/add_premium <user_id>` यूज़ करो ना! 😉")
            return
        
        user_id = int(parts[1])
        await add_premium_user(user_id, months=5)
        await message.reply_text(f"यूज़र {user_id} को 5 महीने के लिए प्रीमियम बना दिया है! मज़े करो! ✨")
    except ValueError:
        await message.reply_text("अरे, user_id नंबर में होना चाहिए! 😤")
    except Exception as e:
        await message.reply_text(f"कुछ गड़बड़ हो गई यार: {e} 😬")

@app.on_message(filters.command("broadcast") & filters.user(BOT_OWNER_ID))
async def broadcast_message_owner(client: Client, message: Message):
    broadcast_text = message.text.split(None, 1)[1] if len(message.text.split(None, 1)) > 1 else None
    if not broadcast_text:
        await message.reply_text("ब्रॉडकास्ट करने के लिए कुछ लिखो भी तो! खाली मैसेज क्यों भेज रहे हो? 🙄")
        return

    # Get all non-premium users and groups
    # This simplified broadcast will send to all users who have ever started the bot,
    # and all groups connected, then filter out premium ones.
    # For production, fetch IDs from premium_users_collection and connected_groups_collection more intelligently.
    
    # Get all private chat users (who started bot)
    # Note: Fetching all chat_ids from MongoDB for broadcast can be slow if there are many.
    # A more efficient way is to store all chat IDs in a dedicated collection.
    
    # For demo, let's just use existing premium user IDs and connected groups.
    all_user_ids = [user['_id'] for user in await premium_users_collection.find().to_list(length=None)]
    all_group_ids = [group['_id'] for group in await connected_groups_collection.find().to_list(length=None)]

    sent_count = 0
    # Send to non-premium users in private chat
    for user_id in all_user_ids:
        if not await is_premium(user_id):
            try:
                await app.send_message(user_id, broadcast_text)
                sent_count += 1
                await asyncio.sleep(0.1) # To avoid flood limits
            except Exception as e:
                print(f"Could not send broadcast to user {user_id}: {e}")
    
    # Send to non-premium groups
    for group_id in all_group_ids:
        group_data = await connected_groups_collection.find_one({'_id': group_id})
        if group_data and not await is_premium(group_data.get('connected_admin_id')):
             try:
                await app.send_message(group_id, broadcast_text)
                sent_count += 1
                await asyncio.sleep(0.1) # To avoid flood limits
             except Exception as e:
                print(f"Could not send broadcast to group {group_id}: {e}")

    await message.reply_text(f"ब्रॉडकास्ट मैसेज भेज दिया गया है (नॉन-प्रीमियम यूज़र्स/ग्रुप्स को)! कुल {sent_count} मैसेज भेजे गए। 😉")

@app.on_message(filters.command("connect") & filters.private)
async def connect_group_command(client: Client, message: Message):
    user_id = message.from_user.id
    if not await is_premium(user_id):
        await message.reply_text("ग्रुप कनेक्ट करने के लिए आपको प्रीमियम लेना होगा! 😉")
        return
    
    try:
        parts = message.text.split()
        if len(parts) != 2:
            await message.reply_text("गलत फॉर्मेट! `/connect <group_id>` यूज़ करो ना! 😉")
            return
        
        group_id = int(parts[1])
        admin_id = message.from_user.id

        # Verify bot is in the group and user is an admin in that group
        try:
            bot_member = await app.get_chat_member(group_id, app.me.id)
            if bot_member.status == 'left':
                await message.reply_text("मैं इस ग्रुप में नहीं हूँ! पहले मुझे ग्रुप में ऐड करो ना! 🥺")
                return
            
            admin_member = await app.get_chat_member(group_id, admin_id)
            if admin_member.status not in ['administrator', 'creator']:
                await message.reply_text("तुम इस ग्रुप के एडमिन नहीं हो! मैं सिर्फ़ एडमिन्स से ही कनेक्ट होती हूँ! 😉")
                return

        except Exception as e:
            await message.reply_text(f"ग्रुप चेक करते समय कुछ गड़बड़ हो गई यार: {e} 😬")
            return
        
        # Save connection data
        await save_connected_group_settings(group_id, {'connected_admin_id': admin_id, 'settings': {'chat_on': True, 'welcome_message': '', 'rules': '', 'anti_spam': False}})
        await message.reply_text(f"ग्रुप `{group_id}` को आपके अकाउंट से कनेक्ट कर दिया है! अब आप ग्रुप सेटिंग्स एक्सेस कर सकते हैं. 🎉", parse_mode="Markdown")
    except ValueError:
        await message.reply_text("अरे, group_id नंबर में होना चाहिए! 😤")
    except Exception as e:
        await message.reply_text(f"कुछ गड़बड़ हो गई यार: {e} 😬")


# --- Group Management Commands (Premium Admin Only) ---
@app.on_message(filters.command(["kick", "ban", "mute", "unmute", "warn", "unwarn"]) & filters.group)
async def handle_group_commands(client: Client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Check if the user is an admin and premium
    try:
        chat_member = await app.get_chat_member(chat_id, user_id)
        if not (chat_member.status in ['administrator', 'creator'] and await is_premium(user_id)):
            await message.reply_text("माफ़ करना, यह कमांड सिर्फ प्रीमियम एडमिन्स के लिए है! 😉")
            return
        
        # Check if bot has necessary permissions
        bot_member = await app.get_chat_member(chat_id, app.me.id)
        if not bot_member.status in ['administrator', 'creator']:
             await message.reply_text("मैं यह नहीं कर पाऊँगी, मेरे पास पर्याप्त परमिशन नहीं है! मुझे एडमिन बनाओ ना! 🥺")
             return

    except Exception as e:
        print(f"Error checking admin/bot status: {e}")
        await message.reply_text("कुछ गड़बड़ हो गई, मैं तुम्हारी एडमिन स्टेटस चेक नहीं कर पा रही! 😬")
        return

    command = message.text.split()[0].lower()
    target_user = None

    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    elif len(message.text.split()) > 1:
        # Try to parse user ID from command, or mention
        try:
            target_user_id = int(message.text.split()[1])
            target_user = await app.get_users(target_user_id)
        except ValueError:
            await message.reply_text("किस पर कमांड चलानी है? मुझे बताओ ना! 🤷‍♀️ (रिप्लाई करो या यूज़र ID/मेंशन दो)")
            return

    if not target_user:
        await message.reply_text("किस पर कमांड चलानी है? मुझे बताओ ना! 🤷‍♀️ (रिप्लाई करो या यूज़र ID/मेंशन दो)")
        return

    target_user_mention = f"@{target_user.username}" if target_user.username else target_user.first_name

    try:
        if command == '/kick':
            if not bot_member.can_restrict_members:
                await message.reply_text("मेरे पास यूज़र्स को किक करने की परमिशन नहीं है! 😥")
                return
            await app.kick_chat_member(chat_id, target_user.id)
            await message.reply_text(f"अरे जाओ ना! अब आपकी जगह नहीं यहाँ! 🤭 {target_user_mention}")
        elif command == '/ban':
            if not bot_member.can_restrict_members:
                await message.reply_text("मेरे पास यूज़र्स को बैन करने की परमिशन नहीं है! 😥")
                return
            await app.ban_chat_member(chat_id, target_user.id)
            await message.reply_text(f"अब नहीं आ पाओगे! हमेशा के लिए आउट! 🙅‍♀️ {target_user_mention}")
        elif command == '/mute':
            if not bot_member.can_restrict_members:
                await message.reply_text("मेरे पास यूज़र्स को म्यूट करने की परमिशन नहीं है! 😥")
                return
            # Mute for 1 hour (3600 seconds)
            await app.restrict_chat_member(chat_id, target_user.id, ChatPermissions(), until_date=int(time.time() + 3600))
            await message.reply_text(f"चुप हो जाओ! अब थोड़ा आराम करो! 🤫 {target_user_mention}")
        elif command == '/unmute':
            if not bot_member.can_restrict_members:
                await message.reply_text("मेरे पास यूज़र्स को अनम्यूट करने की परमिशन नहीं है! 😥")
                return
            await app.restrict_chat_member(chat_id, target_user.id, ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True))
            await message.reply_text(f"ठीक है! अब तुम बोल सकते हो! 🥳 {target_user_mention}")
        elif command == '/warn':
            # This would involve a 'warnings' counter in database for the user
            await message.reply_text(f"उफ्फ! ये गलत बात है! अगली बार ऐसा मत करना!😠 {target_user_mention}")
        elif command == '/unwarn':
            # This would involve resetting a 'warnings' counter
            await message.reply_text(f"चलो, एक गलती माफ़! 😉 {target_user_mention}")
    except Exception as e:
        await message.reply_text(f"अरे, मैं यह नहीं कर पाई! शायद मेरे पास परमिशन नहीं है या कुछ और गड़बड़ है: {e} 😥")


# --- Learning and Responding to Messages ---
# Changed ~filters.edited to ~filters.via_bot to fix AttributeError
@app.on_message(filters.text & filters.group & ~filters.via_bot)
async def learn_and_respond(client: Client, message: Message):
    chat_id = message.chat.id
    message_text = message.text.lower()

    # Basic filter: ignore links, mentions, and commands for learning
    message_text_filtered = re.sub(r'http\S+|www\S+|@\S+|/\w+', '', message_text).strip()
    if not message_text_filtered: # If message is empty after filtering or only contained filtered content
        return

    # Get existing learning data for the group
    group_data = await get_group_learning_data(chat_id)
    learning_deque = group_data['phrases']

    # Add message to learning data
    learning_deque.append(message_text_filtered)
    await save_group_learning_data(chat_id, learning_deque)

    # Simplified response generation:
    if random.random() < 0.3: # 30% chance to respond
        sassy_replies = [
            "हाँ यार!", "सही कहा! 😉", "बिलकुल!", "मज़ेदार!", "और बताओ?",
            "क्या बात है!", "हाहा!", "सच में?", "ठीक है!", "सही बात! 👍",
            "अरे वाह!", "नाइस!", "क्यूट!", "क्या बोल दिया!", "मस्त!",
            "उफ्फ!", "समझ गई! 🤔", "जी जी!", "ओके! 👌"
        ]
        
        chosen_reply = random.choice(sassy_replies) # Default to a generic sassy reply

        # Try to pick a relevant reply from learned data if available
        # This is a very basic attempt. A true learning response would be much more complex.
        if learning_deque:
            # Simple approach: pick a random previous phrase that is short
            short_learned_phrases = [p for p in learning_deque if 1 <= len(p.split()) <= 5]
            if short_learned_phrases:
                chosen_reply = random.choice(short_learned_phrases)
            else:
                chosen_reply = random.choice(sassy_replies) # Fallback if no short phrases learned

        # Simulate sticker usage occasionally
        sticker_ids = [
            'CAACAgIAAxkBAAEX2VNmZm4a2t2192923923923923923923923923923923', # Replace with actual sticker IDs
            'CAACAgIAAxkBAAEX2VNmZm4a2t2192923923923923923923923923923924', # Example sticker
            'CAACAgIAAxkBAAEX2VNmZm4a2t2192923923923923923923923923923925', # Example sticker
            # ... add more sticker IDs that fit the sassy/cute tone
        ]
        
        if random.random() < 0.2 and sticker_ids: # 20% chance for sticker if sticker_ids are available
            await message.reply_sticker(random.choice(sticker_ids))
        else:
            await message.reply_text(chosen_reply)

# --- Ad/Promotion for Non-Premium Users (Randomly) ---
# Changed ~filters.edited to ~filters.via_bot
@app.on_message(filters.text & filters.group & ~filters.via_bot)
async def send_ad_to_non_premium(client: Client, message: Message):
    # Only send ads if the message sender is not premium and there's a 5% chance.
    if not await is_premium(message.from_user.id) and random.random() < 0.05:
        ads = [
            f"अरे यार, यहाँ क्यों बोर हो रहे हो? हमारी मूवी वाली गैंग **[@istreamx]({ISTREAMX_LINK})** में आओ ना! वहाँ तो धूम मची है! 🍿🎬",
            f"क्या! तुम्हें पता नहीं? सारे लेटेस्ट अपडेट्स तो हमारे **[@asbhai_bsr]({MANDATORY_CHANNEL_LINK})** चैनल पर मिलते हैं! जल्दी से जॉइन कर लो! 🏃‍♀️💨",
            f"प्रीमium ऐप्स चाहिए? फिकर नॉट! सीधे **[@aspremiumapps]({ASPREMIUMAPPS_LINK})** पर आओ ना! सब मिलेगा वहाँ! 😉",
            f"अपनी As ki Angel को और भी स्मार्ट और बिना एड्स के चाहते हो? **💎 प्रीमियम लो ना!** `/start` करके देखो! 😉"
        ]
        await message.reply_text(random.choice(ads), parse_mode="Markdown")

# --- Keep-Alive Function ---
async def keep_alive():
    """Sends a periodic message to the bot owner to keep the bot active."""
    # Ensure BOT_OWNER_ID is correctly set for this to work
    if str(BOT_OWNER_ID) == 'YOUR_OWNER_ID_HERE':
        print("Keep-alive: BOT_OWNER_ID not set, cannot send messages.")
        return

    while True:
        try:
            # You can change this message or send it to a private log channel
            await app.send_message(BOT_OWNER_ID, "As ki Angel is awake! (Keep-alive ping from Koyeb)")
            print("Keep-alive: Sent message to owner.")
        except Exception as e:
            print(f"Keep-alive failed to send message: {e}")
        await asyncio.sleep(60 * 5) # हर 5 मिनट में मैसेज भेजो

# --- Start the bot ---
async def main():
    print("As ki Angel bot (Pyrogram) is starting...")
    await app.start()
    print("As ki Angel bot is online!")
    
    # Start the keep-alive task in the background
    asyncio.create_task(keep_alive())
    
    # Keep the bot running indefinitely
    await asyncio.Event().wait() 

if __name__ == "__main__":
    asyncio.run(main())
