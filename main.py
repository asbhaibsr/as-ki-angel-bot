import os
import telebot
import json
import time
from collections import deque

# --- Configuration ---
# Get your bot token from environment variables (will be set on Koyeb)
BOT_TOKEN = os.getenv('BOT_TOKEN')
# Replace with your actual channel username (without @)
MANDATORY_CHANNEL_USERNAME = os.getenv('MANDATORY_CHANNEL_USERNAME', 'asbhai_bsr')
MANDATORY_CHANNEL_LINK = f"https://t.me/{MANDATORY_CHANNEL_USERNAME}"
OFFICIAL_GROUP_LINK = os.getenv('OFFICIAL_GROUP_LINK', 'https://t.me/asbhai_bsr') # Assuming same as mandatory for now
ISTREAMX_LINK = os.getenv('ISTREAMX_LINK', 'https://t.me/istreamx')
ASPREMIUMAPPS_LINK = os.getenv('ASPREMIUMAPPS_LINK', 'https://t.me/aspremiumapps')
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', 'YOUR_OWNER_ID_HERE')) # Replace with your Telegram User ID

# Bot initialization
if not BOT_TOKEN:
    print("Error: BOT_TOKEN environment variable not set.")
    exit()

bot = telebot.TeleBot(BOT_TOKEN)

# --- Bot Learning & Memory (Simplified for demonstration) ---
# This is a very basic in-memory learning. For a real bot,
# you'd need a persistent database (e.g., SQLite, PostgreSQL)
# to store learning data and premium status across restarts.
# Max memory for learning (number of message-reply pairs)
MAX_LEARNING_MEMORY = 1000
# Example: group_id -> deque of (learned_phrase, learned_reply, is_sticker)
GROUP_LEARNING_DATA = {}
# Example: user_id -> {'premium_until': timestamp}
PREMIUM_USERS = {}
# Example: chat_id -> {'connected_admin_id': admin_id, 'settings': {}}
CONNECTED_GROUPS = {}

# In a real scenario, these would be loaded from a database on startup
# and saved periodically or on change.

def check_premium(user_id):
    """Checks if a user has an active premium subscription."""
    if user_id == BOT_OWNER_ID: # Owner is always premium
        return True
    
    premium_data = PREMIUM_USERS.get(user_id)
    if premium_data and premium_data.get('premium_until', 0) > time.time():
        return True
    return False

def check_member_status(user_id, chat_id):
    """Checks if a user is a member of the mandatory channel."""
    try:
        member = bot.get_chat_member(f"@{MANDATORY_CHANNEL_USERNAME}", user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error checking channel membership for {user_id}: {e}")
        return False

def get_chat_type(message):
    """Helper to determine if it's a private or group chat."""
    if message.chat.type in ['group', 'supergroup']:
        return "group"
    elif message.chat.type == 'private':
        return "private"
    return "unknown"

# --- Bot's Fun & Sassy Tone ---
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
        "* **⚡️ सुपर-फास्ट सीखना और जवाब देना:** मैं और भी तेज़ी से सीखूँगी और तुम्हारे हर मैसेज पर झटपट जवाब दूँगी! मज़ा आएगा ना?\n"
        "* **🧠 दिमाग़ थोड़ा बड़ा हो जाएगा:** मेरा दिमाग थोड़ा और बड़ा हो जाएगा, जिससे मैं ग्रुप की बहुत सारी पुरानी बातें याद रख पाऊँगी, "
        "ताकि मैं हमेशा तुमसे सबसे अच्छी बातें करूँ!\n"
        "* **🎭 और भी प्यारे अंदाज़:** प्रीमियम में मैं तुम्हें कुछ और खास 'मूड्स' या 'पर्सनालिटी' के ऑप्शन दूँगी, "
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

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    # Check if user is already a member of the channel
    if not check_member_status(user_id, MANDATORY_CHANNEL_USERNAME):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("Go to Channel", url=MANDATORY_CHANNEL_LINK))
        markup.add(telebot.types.InlineKeyboardButton("✅ I've Joined!", callback_data='check_join'))
        
        bot.send_message(
            message.chat.id,
            "Hi there, friend! 👋 आगे बढ़ने से पहले, ज़रा मेरे परिवार का हिस्सा बनो ना! "
            f"मेरे मेन चैनल **@{MANDATORY_CHANNEL_USERNAME}** को जॉइन करो और फिर वापस आकर मुझे बताओ! ✨",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    else:
        # User is already a member, send full welcome
        send_full_welcome(message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == 'check_join')
def check_join_callback(call):
    user_id = call.from_user.id
    if check_member_status(user_id, MANDATORY_CHANNEL_USERNAME):
        bot.answer_callback_query(call.id, "वाह! तुम तो जॉइन कर चुके हो! अब आगे बढ़ो! 🎉")
        send_full_welcome(call.message.chat.id)
    else:
        bot.answer_callback_query(call.id, "अभी तक जॉइन नहीं किया? ज़रा फिर से चेक करो ना! 😉")

def send_full_welcome(chat_id):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("➕ Add Me to Group!", url=f"https://t.me/{bot.get_me().username}?startgroup=true"))
    markup.add(telebot.types.InlineKeyboardButton("ℹ️ Know My Features", callback_data='features'))
    markup.add(telebot.types.InlineKeyboardButton("🏢 Join Official Group", url=OFFICIAL_GROUP_LINK))
    markup.add(telebot.types.InlineKeyboardButton("💎 Get Premium!", callback_data='get_premium'))
    markup.add(telebot.types.InlineKeyboardButton("⚙️ Group Settings", callback_data='group_settings')) # This button needs /connect to work
    
    bot.send_message(
        chat_id,
        get_sassy_welcome_message(),
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == 'features')
def send_features(call):
    bot.answer_callback_query(call.id, "फीचर्स जानने के लिए तैयार हो? 😉")
    features_text = (
        "**As ki Angel: आपकी अपनी, मज़ेदार और स्मार्ट दोस्त!**\n\n"
        "**1. As ki Angel का स्मार्ट दिमाग और मज़ेदार अंदाज़:**\n"
        "* **सिर्फ़ ग्रुप की बातों से सीखती है:** मैं तुम्हारे ग्रुप में होने वाली हर चैट, हर मैसेज के **शब्दों** को बड़े ध्यान से पढ़ती हूँ और उनसे सीखती हूँ.\n"
        "* **लिंक्स और नाम इग्नोर करती है:** अगर तुम कोई लिंक या किसी को @टैग करते हो, तो मैं उन चीज़ों को **बिलकुल नहीं सीखती**.\n"
        "* **अपनी मेमोरी खुद मैनेज करती है:** जब मेरा दिमाग **100% भर जाता है**, तो मैं खुद ही **सबसे पुराना 50% डेटा मिटा देती हूँ**.\n"
        "* **छोटे और क्यूट जवाब:** मैं हमेशा **1 से 5 शब्दों के बहुत छोटे और मीठे जवाब** देती हूँ.\n"
        "* **स्टिकर्स भी भेजती है:** मैं सही मौक़े पर **प्यारे-प्यारे स्टिकर्स** भी भेजती हूँ.\n"
        "* **तुम्हारे जैसे ही बोलती है:** अगर तुम्हारे ग्रुप में लोग थोड़े **कैजुअल या इनफॉर्मल शब्द** (और कभी-कभी "गालियाँ" भी) इस्तेमाल करते हैं, तो मैं उनको **सीख लेती हूँ** और उसी अंदाज़ में जवाब देती हूँ.\n"
        "* **शायरी भी सुनाती है:** अगर ग्रुप में कोई धांसू शायरी शेयर होती है, तो मैं उसको **याद रख लेती हूँ** और सही मौक़े पर **छोटी शायरी** सुना सकती हूँ.\n"
        "* **तुम्हारी अपनी As ki Angel:** मेरी पूरी बातचीत में तुम्हें एक **प्यारा, शरारती और बिल्कुल अपनी लड़की दोस्त वाला अंदाज़** दिखेगा.\n\n"
        "**2. As ki Angel से पहली मुलाकात (`/start` Command):**\n"
        "* चैनल जॉइन करना ज़रूरी है.\n"
        "* वेलकम मैसेज में बटन्स होते हैं: Add to Group, Know My Features, Join Official Group, Get Premium, Group Settings.\n\n"
        "**3. प्रीमियम सिस्टम (More Fun & Power!):**\n"
        "* **प्रीमियम प्लान:** 500 Rs. में 5 महीने तक अनलिमिटेड मस्ती.\n"
        "* **फायदे:** सुपर-फास्ट सीखना, बड़ा दिमाग, प्यारे अंदाज़, कस्टम स्टिकर, सीक्रेट ग्रुप रिपोर्ट्स, नो एड्स, एक्सक्लूसिव सपोर्ट.\n"
        "* **पेमेंट:** UPI ID - `arsadsaifi8272@ibl`\n"
        "* **एड्स (नॉन-प्रीमियम):** कभी-कभी मस्ती में प्रमोशन वाले मैसेज भी भेज देती हूँ (जैसे @istreamx, @asbhai_bsr, @aspremiumapps).\n\n"
        "**4. ग्रुप मैनेजमेंट सेटिंग्स (For Premium Admins Only):**\n"
        "* `Group Settings` बटन `/connect` कमांड के बाद काम करेगा.\n"
        "* इसमें आप बॉट की चैट ON/OFF कर सकते हैं, वेलकम मैसेज, रूल्स, एंटी-स्पैम फिल्टर और लर्निंग डेटा रीसेट कर सकते हैं.\n\n"
        "**5. ग्रुप मैनेजमेंट कमांड्स (For Premium Admins Only):**\n"
        "* `/kick`, `/ban`, `/mute`, `/unmute`, `/warn`, `/unwarn` जैसी कमांड्स पर मैं मज़ेदार रिप्लाई देती हूँ.\n\n"
        "**6. ब्रॉडकास्ट सिस्टम (For Bot Owner Only):**\n"
        "* `/broadcast` कमांड से बॉट ओनर सभी नॉन-प्रीमियम यूज़र्स और ग्रुप्स को मैसेज भेज सकता है (प्रीमियम यूज़र्स को नहीं)."
    )
    bot.send_message(call.message.chat.id, features_text, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == 'get_premium')
def send_premium_info(call):
    bot.answer_callback_query(call.id, "प्रीमियम? क्या बात है! ✨")
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("💵 Send Payment Proof (@asbhaibsr)", url="https://t.me/asbhaibsr"))
    bot.send_message(call.message.chat.id, get_premium_message(), reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == 'group_settings')
def send_group_settings_info(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    if get_chat_type(call.message) == "private":
        # Check if this private chat is connected to a group and user is admin of that group
        # This part requires more complex logic involving storing connected groups
        # For now, a simplified message.
        bot.answer_callback_query(call.id, "ग्रुप सेटिंग्स के लिए आपको पहले बॉट को अपने ग्रुप से `/connect` करना होगा और आपका प्रीमियम होना ज़रूरी है! 😉")
        bot.send_message(chat_id, "ग्रुप सेटिंग्स यहाँ से एक्सेस करने के लिए, आपको अपने प्रीमियम ग्रुप में रहते हुए मुझे `/connect` कमांड के साथ ग्रुप ID भेजनी होगी.")
    else:
        bot.answer_callback_query(call.id, "यह बटन सिर्फ प्राइवेट चैट में काम करता है, वो भी जब आपने मुझे अपने ग्रुप से /connect किया हो! 😉")


# --- Bot Owner Commands ---
@bot.message_handler(commands=['add_premium'], func=lambda message: message.from_user.id == BOT_OWNER_ID)
def add_premium(message):
    try:
        parts = message.text.split()
        if len(parts) != 2:
            bot.send_message(message.chat.id, "गलत फॉर्मेट! `/add_premium <user_id>` यूज़ करो ना! 😉")
            return
        
        user_id = int(parts[1])
        # Premium for 5 months
        premium_until = time.time() + (5 * 30 * 24 * 60 * 60) 
        PREMIUM_USERS[user_id] = {'premium_until': premium_until}
        bot.send_message(message.chat.id, f"यूज़र {user_id} को 5 महीने के लिए प्रीमियम बना दिया है! मज़े करो! ✨")
    except ValueError:
        bot.send_message(message.chat.id, "अरे, user_id नंबर में होना चाहिए! 😤")
    except Exception as e:
        bot.send_message(message.chat.id, f"कुछ गड़बड़ हो गई यार: {e} 😬")

@bot.message_handler(commands=['broadcast'], func=lambda message: message.from_user.id == BOT_OWNER_ID)
def broadcast_message(message):
    broadcast_text = " ".join(message.text.split()[1:])
    if not broadcast_text:
        bot.send_message(message.chat.id, "ब्रॉडकास्ट करने के लिए कुछ लिखो भी तो! खाली मैसेज क्यों भेज रहे हो? 🙄")
        return

    # This is a placeholder. In a real bot, you'd iterate through
    # all non-premium users and non-premium groups from your database.
    # For this example, we will just print a confirmation.
    bot.send_message(message.chat.id, f"ब्रॉडकास्ट मैसेज भेज दिया जाएगा: '{broadcast_text}' (नॉन-प्रीमियम यूज़र्स/ग्रुप्स को) 😉")


# --- Group Management Commands (Premium Admin Only) ---
# This part requires proper checking for admin status and group connection
# For simplicity, these are just placeholders showing the response.
# In a real bot, you'd add actual user/chat management logic.
@bot.message_handler(commands=['kick', 'ban', 'mute', 'unmute', 'warn', 'unwarn'])
def handle_group_commands(message):
    # This is a very basic check. Real implementation needs:
    # 1. Check if the user sending command is a group admin.
    # 2. Check if the group is a premium group (if applicable).
    # 3. Actual Telegram API calls for kick, ban, etc.
    
    command = message.text.split()[0]
    target_user_mention = message.text.split()[-1] if len(message.text.split()) > 1 else ""

    if command == '/kick':
        bot.send_message(message.chat.id, f"अरे जाओ ना! अब आपकी जगह नहीं यहाँ! 🤭 {target_user_mention}")
    elif command == '/ban':
        bot.send_message(message.chat.id, f"अब नहीं आ पाओगे! हमेशा के लिए आउट! 🙅‍♀️ {target_user_mention}")
    elif command == '/mute':
        bot.send_message(message.chat.id, f"चुप हो जाओ! अब थोड़ा आराम करो! 🤫 {target_user_mention}")
    elif command == '/unmute':
        bot.send_message(message.chat.id, f"ठीक है! अब तुम बोल सकते हो! 🥳 {target_user_mention}")
    elif command == '/warn':
        bot.send_message(message.chat.id, f"उफ्फ! ये गलत बात है! अगली बार ऐसा मत करना! 😠 {target_user_mention}")
    elif command == '/unwarn':
        bot.send_message(message.chat.id, f"चलो, एक गलती माफ! 😉 {target_user_mention}")

# --- Learning and Responding to Messages ---
@bot.message_handler(func=lambda message: get_chat_type(message) == 'group' and message.text)
def learn_and_respond(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    message_text = message.text.lower() # Convert to lowercase for learning

    # Basic filter: ignore links, mentions, and commands for learning
    if "http://" in message_text or "https://" in message_text or "@" in message_text or message_text.startswith('/'):
        return

    # Add message to learning data (simplified for this example)
    if chat_id not in GROUP_LEARNING_DATA:
        GROUP_LEARNING_DATA[chat_id] = deque(maxlen=MAX_LEARNING_MEMORY)
    
    # Store the last message for potential reply learning (very basic)
    # This needs a more sophisticated approach for actual context-based replies.
    # For now, we'll store the message itself.
    GROUP_LEARNING_DATA[chat_id].append((message_text, None, False)) # (phrase, reply, is_sticker)

    # Simplified response generation:
    # In a real bot, you'd analyze the current message and find a
    # learned short reply or sticker from GROUP_LEARNING_DATA.
    # This is a complex part and would involve pattern matching,
    # frequency analysis, and potentially sentiment.

    # For this basic example, let's make it respond randomly sometimes
    # or with pre-defined short sassy replies.
    import random
    if random.random() < 0.3: # 30% chance to respond
        sassy_replies = [
            "हाँ यार!", "सही कहा! 😉", "बिलकुल!", "मज़ेदार!", "और बताओ?",
            "क्या बात है!", "हाहा!", "सच में?", "ठीक है!", "सही बात! 👍",
            "अरे वाह!", "नाइस!", "क्यूट!", "क्या बोल दिया!", "मस्त!",
            "उफ्फ!", "समझ गई! 🤔", "जी जी!", "ओके! 👌"
        ]
        chosen_reply = random.choice(sassy_replies)
        
        # Simulate sticker usage occasionally
        if random.random() < 0.2: # 20% chance for sticker
            # In a real bot, you'd map messages to specific sticker IDs
            sticker_ids = [
                'CAACAgIAAxkBAAEX2VNmZm4a2t2192923923923923923923923923923923', # Example sticker ID, replace with actual
                'CAACAgIAAxkBAAEX2VNmZm4a2t2192923923923923923923923923923924', # Another example
                # ... add more sticker IDs that fit the sassy/cute tone
            ]
            bot.send_sticker(chat_id, random.choice(sticker_ids))
        else:
            bot.send_message(chat_id, chosen_reply)

# --- Start the bot ---
print("As ki Angel bot is starting...")
bot.polling(none_stop=True)

