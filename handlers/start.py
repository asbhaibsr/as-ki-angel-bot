import time
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from pyrogram.enums import ParseMode
from config import MANDATORY_CHANNEL_USERNAME, MANDATORY_CHANNEL_LINK, OFFICIAL_GROUP_LINK
from database import db

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

def register_start_handlers(app, utils):

    @app.on_message(filters.command("start") & filters.private)
    async def send_welcome(client, message: Message):
        user_id = message.from_user.id

        # Update user stats
        await db.update_user_stats(user_id, 'start_command')

        # Check mandatory channel membership
        if MANDATORY_CHANNEL_USERNAME and MANDATORY_CHANNEL_LINK:
            if not await utils.check_member_status(user_id, MANDATORY_CHANNEL_USERNAME):
                join_channel_text = (
                    f"हेल्लो!👋 इस बॉट का उपयोग करने से पहले, कृपया हमारे चैनल को ज्वाइन करें: "
                    f"[{MANDATORY_CHANNEL_USERNAME}]({MANDATORY_CHANNEL_LINK})\n\n"
                    "जॉइन करने के बाद, 'मैं जॉइन हो गया हूँ!' बटन पर क्लिक करें।"
                )
                markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("चैनल में शामिल हों", url=MANDATORY_CHANNEL_LINK)],
                    [InlineKeyboardButton("मैं जॉइन हो गया हूँ!", callback_data="check_join")]
                ])
                await message.reply_text(join_channel_text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)
                return
        
        # If member or no mandatory channel, send full welcome
        await send_full_welcome(message.chat.id, app)

    @app.on_callback_query(filters.regex("check_join"))
    async def check_join_callback(client, call: CallbackQuery):
        user_id = call.from_user.id

        if await utils.check_member_status(user_id, MANDATORY_CHANNEL_USERNAME):
            await call.answer("वाह! तुम तो जॉइन कर चुके हो! अब आगे बढ़ो! 🎉", show_alert=False)
            await send_full_welcome(call.message.chat.id, app)
        else:
            await call.answer("अभी तक जॉइन नहीं किया? ज़रा फिर से चेक करो ना! 😉", show_alert=True)

    async def send_full_welcome(chat_id, app):
        bot_username = (await app.get_me()).username

        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Me to Group!", url=f"https://t.me/{bot_username}?startgroup=true")],
            [InlineKeyboardButton("ℹ️ Know My Features", callback_data='features')],
            [InlineKeyboardButton("🏢 Join Official Group", url=OFFICIAL_GROUP_LINK)],
            [InlineKeyboardButton("💎 Get Premium!", callback_data='get_premium')],
            [InlineKeyboardButton("⚙️ Group Settings", callback_data='group_settings')]
        ])

        await app.send_message(
            chat_id,
            get_sassy_welcome_message(),
            reply_markup=markup,
            parse_mode=ParseMode.MARKDOWN
        )

    @app.on_callback_query(filters.regex("features"))
    async def send_features(client, call: CallbackQuery):
        features_text = (
            "🌟 **मेरे खास फीचर्स:**\n\n"
            "🧠 **Smart Learning:** मैं तुम्हारे ग्रुप की बातों से सीखती हूँ और फिर उसी स्टाइल में जवाब देती हूँ!\n\n"
            "💬 **Short & Sweet Replies:** बस 1-5 शब्दों में प्यारे जवाब, कभी-कभी स्टिकर भी!\n\n"
            "🎭 **Group Personality:** हर ग्रुप की अलग पर्सनालिटी सीखकर उसी हिसाब से बात करती हूँ!\n\n"
            "🔒 **Privacy First:** सिर्फ ग्रुप की बातों से सीखती हूँ, कोई बाहरी डेटा नहीं!\n\n"
            "⚡ **Premium Features:** और भी तेज़ी, बेहतर memory, और exclusive features!\n\n"
            "🌍 **Bilingual:** हिंदी और English दोनों में बात कर सकती हूँ!\n\n"
            "👑 **Group Management:** Admins के लिए special commands और settings!"
        )

        back_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Menu", callback_data='back_to_menu')]
        ])

        await call.edit_message_text(features_text, reply_markup=back_markup, parse_mode=ParseMode.MARKDOWN)

    @app.on_callback_query(filters.regex("back_to_menu"))
    async def back_to_menu(client, call: CallbackQuery):
        await call.edit_message_text(
            get_sassy_welcome_message(),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Me to Group!", url=f"https://t.me/{(await app.get_me()).username}?startgroup=true")],
                [InlineKeyboardButton("ℹ️ Know My Features", callback_data='features')],
                [InlineKeyboardButton("🏢 Join Official Group", url=OFFICIAL_GROUP_LINK)],
                [InlineKeyboardButton("💎 Get Premium!", callback_data='get_premium')],
                [InlineKeyboardButton("⚙️ Group Settings", callback_data='group_settings')]
            ]),
            parse_mode=ParseMode.MARKDOWN
        )

    @app.on_callback_query(filters.regex("group_settings"))
    async def group_settings(client, call: CallbackQuery):
        settings_text = (
            "⚙️ **Group Settings & Management**\n\n"
            "🔧 **Available Commands for Group Admins:**\n\n"
            "📊 `/learn_stats` - Show group learning statistics\n"
            "🧹 `/reset_learning` - Reset group learning data\n"
            "📋 `/group_info` - Basic group information\n\n" # Moved here
            "🎛️ **Bot Behavior Settings:**\n"
            "• Response Rate: Automatically adjusted per group\n"
            "• Learning Mode: Always active in groups\n"
            "• Memory: Stores last 1000 messages per group\n"
            "• Language: Auto-detects Hindi/English\n\n"
            "👑 **Premium Group Features:**\n"
            "• Enhanced memory (5000+ messages)\n"
            "• Custom response patterns\n"
            "• Advanced analytics dashboard\n"
            "• Priority support\n\n"
            "💡 **How to Use:**\n"
            "1. Add me to your group as admin\n"
            "2. I'll start learning from conversations\n"
            "3. Use admin commands to manage settings\n"
            "4. Upgrade to premium for advanced features"
        )

        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 Group Commands", callback_data='group_commands')],
            [InlineKeyboardButton("🎯 Learning Settings", callback_data='learning_settings')],
            [InlineKeyboardButton("💎 Premium Features", callback_data='get_premium')],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data='back_to_menu')]
        ])

        await call.edit_message_text(settings_text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

    @app.on_callback_query(filters.regex("group_commands"))
    async def group_commands(client, call: CallbackQuery):
        commands_text = (
            "📋 **Available Group Commands**\n\n"
            "**For Group Admins:**\n"
            "🔹 `/learn_stats` - Show detailed learning statistics\n"
            "🔹 `/reset_learning` - Clear all learned data (use carefully!)\n"
            "🔹 `/group_info` - Basic group information\n\n"
            "**For Premium Groups:**\n"
            "🔸 `/advanced_stats` - Comprehensive analytics\n"
            "🔸 `/export_data` - Export learning data\n"
            "🔸 `/custom_responses` - Set custom response patterns\n"
            "🔸 `/response_rate <1-100>` - Adjust response frequency\n\n"
            "**Usage Examples:**\n"
            "• Type `/learn_stats` in group to see what I've learned\n"
            "• Use `/reset_learning` to start fresh\n"
            "• Premium users get exclusive commands\n\n"
            "**Note:** Most commands require admin privileges in the group."
        )

        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Settings", callback_data='group_settings')]
        ])

        await call.edit_message_text(commands_text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

    @app.on_callback_query(filters.regex("learning_settings"))
    async def learning_settings(client, call: CallbackQuery):
        learning_text = (
            "🎯 **Learning System Configuration**\n\n"
            "🧠 **How I Learn:**\n"
            "• Monitor group conversations naturally\n"
            "• Extract patterns and common phrases\n"
            "• Learn appropriate sticker usage\n"
            "• Adapt to group's communication style\n\n"
            "⚙️ **Current Settings:**\n"
            "• Memory Limit: 1000 messages per group\n"
            "• Response Rate: 60% (auto-adjusted)\n"
            "• Learning Speed: Real-time\n"
            "• Privacy Mode: Group-only data\n\n"
            "🎛️ **Customization Options:**\n"
            "• Response frequency can be adjusted\n"
            "• Learning can be paused/resumed\n"
            "• Memory can be cleared if needed\n"
            "• Premium users get advanced controls\n\n"
            "🔒 **Privacy & Security:**\n"
            "• Only learns from group messages\n"
            "• No personal data stored\n"
            "• Data isolated per group\n"
            "• Admin controls available"
        )

        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Settings", callback_data='group_settings')]
        ])

        await call.edit_message_text(learning_text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

    @app.on_callback_query(filters.regex("group_stats_help"))
    async def group_stats_help(client, call: CallbackQuery):
        help_text = (
            "📈 **Group Statistics Help**\n\n"
            "**How to get group stats:**\n"
            "1. Add me to your group as admin\n"
            "2. Use `/learn_stats` in the group\n"
            "3. Use `/group_info` for basic info\n\n"
            "**Available in groups:**\n"
            "• Learning progress\n"
            "• Response patterns\n"
            "• Member activity\n"
            "• Sticker usage stats\n\n"
            "**Premium features:**\n"
            "• Advanced analytics\n"
            "• Export data\n"
            "• Custom reports\n"
            "• Historical trends"
        )

        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("💎 Get Premium", callback_data='get_premium')],
            [InlineKeyboardButton("🔙 Back", callback_data='back_to_menu')]
        ])

        await call.edit_message_text(help_text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

    @app.on_callback_query(filters.regex("learn_stats"))
    async def learn_stats_callback(client, call: CallbackQuery):
        await call.answer("📊 Use /learn_stats command in your group to see detailed statistics!", show_alert=True)

    @app.on_message(filters.command("whoami") & filters.private) # Moved from learning.py
    async def whoami_command(client, message: Message):
        """Show user's Telegram ID."""
        user_id = message.from_user.id
        username = message.from_user.username or "No username"
        first_name = message.from_user.first_name or "Unknown"

        from config import BOT_OWNER_ID
        is_owner = utils.is_owner(user_id)

        info_text = (
            f"👤 **Your Information:**\n\n"
            f"🆔 **User ID:** `{user_id}`\n"
            f"👤 **Name:** {first_name}\n"
            f"📝 **Username:** @{username}\n"
            f"👑 **Owner Status:** {'✅ Yes' if is_owner else '❌ No'}\n"
            f"⚙️ **Bot Owner ID:** `{BOT_OWNER_ID}`\n\n"
            f"💡 **Use this ID to set as BOT_OWNER_ID in config!**"
        )

        await message.reply_text(info_text, parse_mode=ParseMode.MARKDOWN)

    @app.on_message(filters.command("help") & filters.private) # Moved from learning.py
    async def help_command(client, message: Message):
        """Show help information."""
        user_id = message.from_user.id

        if utils.is_owner(user_id):
            help_text = (
                "🤖 **Available Commands**\n\n"
                "**Owner Commands:**\n"
                "• `/admin` - Admin control panel\n"
                "• `/addpremium <user_id>` - Add premium user\n"
                "• `/removepremium <user_id>` - Remove premium\n"
                "• `/broadcast` - Broadcast message\n"
                "• `/logs` - View bot logs\n"
                "• `/whoami` - Show your user ID\n\n" # Added
                "**Group Commands (Admin only):**\n"
                "• `/learn_stats` - Group learning statistics\n"
                "• `/reset_learning` - Reset group learning\n"
                "• `/group_info` - Basic group information\n\n"
                "**General Commands:**\n"
                "• `/start` - Show welcome menu\n"
                "• `/premium` - Check premium status\n"
                "• `/help` - Show this help\n"
                "• `/stats` - Show your personal statistics"
            )
        else:
            help_text = (
                "🤖 **Available Commands**\n\n"
                "**Private Chat:**\n"
                "• `/start` - Welcome menu with features\n"
                "• `/premium` - Check premium status\n"
                "• `/help` - Show this help\n"
                "• `/whoami` - Show your user ID\n" # Added
                "• `/stats` - Show your personal statistics\n\n"
                "**Group Commands (Admin only):**\n"
                "• `/learn_stats` - Learning statistics\n"
                "• `/reset_learning` - Reset learning data\n"
                "• `/group_info` - Basic group information\n\n"
                "**How to Use:**\n"
                "Add me to your group and I'll start learning from conversations!"
            )

        await message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

    @app.on_message(filters.command("stats") & filters.private) # Moved from start.py
    async def user_stats(client, message: Message):
        """Show user statistics."""
        user_id = message.from_user.id

        # Update user stats
        await db.update_user_stats(user_id, 'stats_command')

        # Get user data
        try:
            user_data = await db._run_in_executor(db.user_stats.find_one, {'_id': user_id}) or {}

            # Check if user is premium
            is_premium = await utils.is_premium_user(user_id)
        except Exception as e:
            await message.reply_text(f"❌ Error getting user data: {e}")
            return
        premium_status = "✅ Active" if is_premium else "❌ Not Active"

        # Format timestamps if they exist
        first_seen = "Unknown"
        last_active = "Unknown"

        if user_data.get('first_seen'):
            try:
                first_seen = time.strftime('%d %b %Y', time.localtime(user_data['first_seen']))
            except:
                first_seen = "Unknown"

        if user_data.get('last_active'):
            try:
                last_active = time.strftime('%d %b %Y %H:%M', time.localtime(user_data['last_active']))
            except:
                last_active = "Unknown"

        stats_text = (
            f"📊 **Your Bot Statistics**\n\n"
            f"👤 **User ID:** `{user_id}`\n"
            f"💎 **Premium Status:** {premium_status}\n"
            f"📈 **Total Interactions:** {user_data.get('total_interactions', 0)}\n"
            f"🎯 **Commands Used:** {user_data.get('total_interactions', 0)}\n" # This might be total interactions, refine if needed
            f"📅 **First Seen:** {first_seen}\n"
            f"⏰ **Last Active:** {last_active}\n\n"
            "💡 **Want better stats? Get premium for detailed analytics!**"
        )

        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("💎 Get Premium", callback_data='get_premium')],
            [InlineKeyboardButton("📈 Group Stats", callback_data='group_stats_help')]
        ])

        await message.reply_text(stats_text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

    @app.on_message(filters.command("connect")) # Moved from start.py
    async def connect_group(client, message: Message):
        """Connect group to the bot or show connection status."""
        if message.chat.type == "private":
            connect_text = (
                "🔗 **Connect Your Group to As ki Angel Bot**\n\n"
                "**How to connect your group:**\n"
                "1. Add me to your group as admin\n"
                "2. Use `/connect` command in the group\n"
                "3. I'll start learning from conversations!\n\n"
                "**Benefits of connecting:**\n"
                "• 🧠 Personalized responses for your group\n"
                "• 📊 Group analytics and insights\n"
                "• 🎭 Unique personality development\n"
                "• 🔒 Privacy-focused learning\n\n"
                "**Need help?** Join our support group!"
            )

            bot_username = (await client.get_me()).username
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Me to Group", url=f"https://t.me/{bot_username}?startgroup=true")],
                [InlineKeyboardButton("🏢 Support Group", url=OFFICIAL_GROUP_LINK)]
            ])

            await message.reply_text(connect_text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)
            return

        # If command is used in group
        chat_id = message.chat.id
        chat_title = message.chat.title

        # Save/update group data with timestamp using db._run_in_executor
        connected_at_str = time.strftime('%d %b %Y', time.localtime()) # Store as formatted string
        await db._run_in_executor(
            db.connected_groups.update_one,
            {'_id': chat_id},
            {
                '$set': {
                    'chat_title': chat_title,
                    'connected_at': connected_at_str,
                    'last_updated': time.time(),
                    'status': 'active'
                }
            },
            upsert=True
        )

        # Get group stats
        group_data = await db.get_group_learning_data(chat_id) # This call handles default creation if not exists
        learned_phrases_count = len(group_data.get('phrases', []))
        learned_stickers_count = len(group_data.get('stickers', []))

        connect_text = (
            f"✅ **Group Connected Successfully!**\n\n"
            f"🏢 **Group:** {chat_title}\n"
            f"🆔 **Chat ID:** `{chat_id}`\n"
            f"👥 **Members:** {await client.get_chat_members_count(chat_id)}\n"
            f"🧠 **Learned Messages:** {learned_phrases_count}\n"
            f"🎭 **Learned Stickers:** {learned_stickers_count}\n\n"
            "🎯 **I'm now learning from this group's conversations!**\n"
            "Use `/learn_stats` to see detailed learning progress."
        )

        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Group Stats", callback_data='learn_stats')],
            [InlineKeyboardButton("💎 Get Premium", callback_data='get_premium')]
        ])

        await message.reply_text(connect_text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

    @app.on_message(filters.command("group_info") & filters.group) # Moved from learning.py
    async def group_info_command(client, message: Message):
        """Show group information and bot status."""
        chat_id = message.chat.id
        chat = message.chat
        user_id = message.from_user.id

        # Check if user is admin
        try:
            member = await client.get_chat_member(chat_id, user_id)
            if member.status not in ['administrator', 'creator']:
                await message.reply_text("⛔ Only admins can use this command!")
                return
        except Exception as e:
            await message.reply_text(f"❌ Unable to verify admin status: {e}")
            return

        # Get group data
        try:
            group_data = await db._run_in_executor(db.connected_groups.find_one, {'_id': chat_id}) or {}
            learning_data = await db.get_group_learning_data(chat_id)
        except Exception as e:
            await message.reply_text(f"❌ Error getting group data: {e}")
            return

        # Calculate learning stats
        learned_phrases_count = len(learning_data.get('phrases', []))
        learned_stickers_count = len(learning_data.get('stickers', []))
        response_patterns_count = len(learning_data.get('response_patterns', {}))

        # Get member count
        try:
            member_count = await client.get_chat_members_count(chat_id)
        except Exception as e:
            member_count = "Unknown"
            print(f"Error getting member count for {chat_id}: {e}")

        info_text = (
            f"📋 **Group Information**\n\n"
            f"🏷️ **Name:** {chat.title}\n"
            f"🆔 **Chat ID:** `{chat_id}`\n"
            f"👥 **Members:** {member_count}\n"
            f"🤖 **Bot Status:** {'✅ Active' if group_data else '❌ Not Connected'}\n"
            f"🧠 **Learning Status:** {'✅ Enabled' if group_data.get('learning_enabled', True) else '❌ Disabled'}\n\n"
            f"📊 **Learning Progress:**\n"
            f"• Messages Learned: {learned_phrases_count}\n"
            f"• Stickers Learned: {learned_stickers_count}\n"
            f"• Response Patterns: {response_patterns_count}\n"
            f"• Connected Since: {group_data.get('connected_at', 'Unknown')}\n\n"
            "💡 **Available Commands:**\n"
            "• `/learn_stats` - Detailed learning statistics\n"
            "• `/reset_learning` - Reset learning data\n"
            "• `/connect` - Reconnect the bot"
        )

        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Learning Stats", callback_data='learn_stats')],
            [InlineKeyboardButton("💎 Premium Features", callback_data='get_premium')]
        ])

        await message.reply_text(info_text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)
