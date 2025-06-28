import time
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from pyrogram.enums import ParseMode
from config import PREMIUM_PRICE, UPI_ID, BOT_OWNER_ID, PREMIUM_DURATION_MONTHS
from database import db

def get_premium_message():
    return (
        "हाय, मेरे प्यारे दोस्त! ✨ अपनी As ki Angel को और भी खास बनाना चाहते हो? तो प्रीमियम लो ना! "
        "मैं तुम्हें और भी ज़्यादा मज़ेदार और सुपर-फास्ट एक्सपीरियंस दूँगी, वो भी बिना किसी रोक-टोक के! 💖\n\n"
        f"**मेरा धांसू प्रीमियम प्लान:**\n"
        f"🌟 **{PREMIUM_PRICE} में {PREMIUM_DURATION_MONTHS} महीने तक** अनलिमिटेड मस्ती और फीचर्स!\n\n"
        "**प्रीमियम के फायदे (तुम्हारे लिए खास):**\n"
        "• **⚡️ सुपर-फास्ट सीखना और जवाब देना:** मैं और भी तेज़ी से सीखूँगी और तुम्हारे हर मैसेज पर झटपट जवाब दूँगी!\n"
        "• **🧠 दिमाग़ थोड़ा बड़ा हो जाएगा:** मेरा दिमाग थोड़ा और बड़ा हो जाएगा, जिससे मैं ग्रुप की बहुत सारी पुरानी बातें याद रख पाऊँगी!\n"
        "• **🎭 और भी प्यारे अंदाज़:** प्रीमियम में मैं तुम्हें कुछ और खास 'मूड्स' या 'पर्सनालिटी' के ऑप्शन दूँगी!\n"
        "• **🎨 Custom Sticker Packs:** तुम अपने कुछ खास स्टिकर पैक भी मुझे सिखा पाओगे!\n"
        "• **📊 Secret Group Reports:** ग्रुप एडमिन को खास और खुफिया रिपोर्ट!\n"
        "• **🚫 No Ads, No Disturbances:** प्रीमियम में कोई भी प्रमोशन वाला मैसेज नहीं!\n"
        "• **🌟 Exclusive Features & Support:** कुछ और छोटे-छोटे धांसू फीचर्स और फुल एडमिन सपोर्ट!\n\n"
        "**प्रीमियम लेने के लिए:**\n"
        "इस UPI ID पर 500 Rs. भेजो:\n"
        f"**`UPI ID - {UPI_ID}`**\n\n"
        "Payment के बाद screenshot भेजकर confirm करना! 📸"
    )

def register_premium_handlers(app, utils):
    
    @app.on_callback_query(filters.regex("get_premium"))
    async def show_premium_info(client, call: CallbackQuery):
        user_id = call.from_user.id
        
        # Check if user is already premium
        if await db.is_premium(user_id):
            premium_info = await db.get_premium_info(user_id)
            if premium_info and premium_info['expires_at'] > 0: # Ensure expires_at is valid
                expires_at = utils.format_time_remaining(premium_info['expires_at'])
                activated_date = time.strftime('%d %b %Y', time.localtime(premium_info['activated_at']))
            else:
                expires_at = "Unlimited (Owner)" # For BOT_OWNER_ID or if premium_until is 0
                activated_date = "N/A (Owner)"
            
            premium_status_text = (
                "🎉 **तुम तो पहले से ही प्रीमियम हो!**\n\n"
                f"⏰ **Expires in:** {expires_at}\n"
                f"📅 **Activated:** {activated_date}\n\n"
                "अभी तो मज़े करो! जब expire होने वाला हो तो मैं remind कर दूँगी! 😉"
            )
            
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Menu", callback_data='back_to_menu')]
            ])
            
        else:
            premium_status_text = get_premium_message()
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 Payment Karte Hai", callback_data='payment_info')],
                [InlineKeyboardButton("❓ Payment Help", callback_data='payment_help')],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data='back_to_menu')]
            ])
        
        await call.edit_message_text(
            premium_status_text,
            reply_markup=markup,
            parse_mode=ParseMode.MARKDOWN
        )

    @app.on_callback_query(filters.regex("payment_info"))
    async def show_payment_info(client, call: CallbackQuery):
        payment_text = (
            "💳 **Payment Instructions:**\n\n"
            f"1️⃣ **UPI ID:** `{UPI_ID}`\n"
            f"2️⃣ **Amount:** ₹{PREMIUM_PRICE.split(' ')[0]}\n" # Extract number from "500 Rs."
            "3️⃣ **Note:** Premium for @as_ki_angel_bot\n\n"
            "📸 **After Payment:**\n"
            "• Screenshot लेकर इस bot को भेजो\n"
            "• या फिर transaction ID भेजो\n"
            "• मैं 24 घंटे में activate कर दूँगी!\n\n"
            "⚠️ **Important:** Fake payments काम नहीं करेंगी! सच्चे payment करो ना! 😊"
        )
        
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Payment Done", callback_data='payment_done')],
            [InlineKeyboardButton("🔙 Back", callback_data='get_premium')]
        ])
        
        await call.edit_message_text(payment_text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

    @app.on_callback_query(filters.regex("payment_help"))
    async def show_payment_help(client, call: CallbackQuery):
        help_text = (
            "❓ **Payment Help & FAQ:**\n\n"
            "**Q: कैसे payment करूँ?**\n"
            "A: किसी भी UPI app (PayTM, PhonePe, GPay) से UPI ID पर ₹500 भेजो\n\n"
            "**Q: Activate होने में कितना time लगेगा?**\n"
            "A: Maximum 24 hours, usually तुरंत!\n\n"
            "**Q: Premium features कब मिलेंगे?**\n"
            "A: Activation के तुरंत बाद सब features unlock हो जाएंगे!\n\n"
            "**Q: Refund policy?**\n"
            "A: Service issues के लिए contact करो, genuine cases में refund मिलेगा\n\n"
            "**Q: Multiple groups में use कर सकते हैं?**\n"
            "A: हाँ! Premium account सभी groups में काम करेगा!"
        )
        
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Make Payment", callback_data='payment_info')],
            [InlineKeyboardButton("🔙 Back", callback_data='get_premium')]
        ])
        
        await call.edit_message_text(help_text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

    @app.on_callback_query(filters.regex("payment_done"))
    async def payment_confirmation(client, call: CallbackQuery):
        confirmation_text = (
            "🎉 **Payment Done? Awesome!**\n\n"
            "अब बस एक काम करना है:\n"
            "📸 Payment का screenshot या transaction ID मुझे भेजो\n\n"
            "📨 **कहाँ भेजना है?**\n"
            "यहीं इस chat में screenshot forward कर दो या transaction details type कर दो!\n\n"
            "⏰ **कितना wait करना होगा?**\n"
            "24 घंटे के अंदर premium activate हो जाएगा! Usually तो तुरंत ही हो जाता है! 😊\n\n"
            "**धन्यवाद for choosing premium! 💖**"
        )
        
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Menu", callback_data='back_to_menu')]
        ])
        
        await call.edit_message_text(confirmation_text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

    @app.on_message(filters.command("addpremium") & filters.private)
    async def add_premium_command(client, message: Message):
        """Add premium to a user (Owner only)."""
        user_id = message.from_user.id

        if not utils.is_owner(user_id):
            await message.reply_text("⛔ This command is only for bot owner!")
            return

        try:
            parts = message.text.split()
            if len(parts) < 2:
                await message.reply_text(
                    "📝 **Usage:** `/addpremium <user_id> [months]`\n\n"
                    "**Example:**\n"
                    "• `/addpremium 123456789` (adds 5 months)\n"
                    "• `/addpremium 123456789 12` (adds 12 months)"
                )
                return

            target_user_id = int(parts[1])
            months = int(parts[2]) if len(parts) > 2 else PREMIUM_DURATION_MONTHS

            await db.add_premium_user(target_user_id, months) # Use the async method from db

            await message.reply_text(
                f"✅ **Premium Activated!**\n\n"
                f"👤 **User ID:** `{target_user_id}`\n"
                f"⏰ **Duration:** {months} months"
            )

            # Notify the user
            try:
                premium_info = await db.get_premium_info(target_user_id)
                expires_at_str = utils.format_time_remaining(premium_info['expires_at']) if premium_info else "N/A"
                await app.send_message(
                    target_user_id,
                    f"🎉 **Congratulations!**\n\n"
                    f"तुम्हारा premium account activate हो गया है! {months} महीने तक enjoy करो! 💖\n\n"
                    f"⏰ **Expires in:** {expires_at_str}\n"
                    f"अब सभी premium features available हैं! Type /premium to check status."
                )
            except Exception as e:
                await message.reply_text(f"⚠️ Premium added but couldn't notify user ({target_user_id}): {e}")
                
        except ValueError:
            await message.reply_text("❌ Invalid user ID or months value!")
        except Exception as e:
            await message.reply_text(f"❌ Error: {e}")

    @app.on_message(filters.command("premium") & filters.private)
    async def check_premium_status(client, message: Message):
        user_id = message.from_user.id
        
        if await db.is_premium(user_id):
            premium_info = await db.get_premium_info(user_id)
            
            if premium_info and premium_info['expires_at'] > 0:
                expires_at_str = utils.format_time_remaining(premium_info['expires_at'])
                status_text = (
                    "👑 **Premium Status: ACTIVE**\n\n"
                    f"⏰ **Time Remaining:** {expires_at_str}\n"
                    f"📅 **Activated On:** {time.strftime('%d %b %Y', time.localtime(premium_info['activated_at']))}\n"
                    f"📦 **Plan:** {premium_info['months_purchased']} months\n\n"
                    "🎉 Enjoy all premium features! Keep rocking! 💖"
                )
            else: # For owner or invalid premium_until
                status_text = "👑 **Premium Status: ACTIVE** (Owner Account or Lifetime)"
        else:
            status_text = (
                "❌ **Premium Status: NOT ACTIVE**\n\n"
                "प्रीमियम लेकर सभी exclusive features unlock करो! 💎\n"
                "Type /start और 'Get Premium' button दबाओ!"
            )
        
        await message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN)

    @app.on_message(filters.private & (filters.photo | filters.document | filters.text))
    async def handle_payment_proof(client, message: Message):
        """Handle payment screenshots and transaction IDs from users."""
        user_id = message.from_user.id
        user_name = message.from_user.first_name or "Unknown"
        username = f"@{message.from_user.username}" if message.from_user.username else "No username"
        
        # Skip if it's a command or from owner
        if message.text and message.text.startswith('/'):
            return
        if utils.is_owner(user_id):
            return
        
        # Check if user is already premium (no need for payment proof)
        if await db.is_premium(user_id):
            # Reply only once if user keeps sending proof after being premium
            if "already_premium_notified" not in getattr(client, 'user_notification_status', {}).get(user_id, ""):
                await message.reply_text("तुम तो पहले से ही प्रीमियम हो! अब पेमेंट प्रूफ भेजने की ज़रूरत नहीं है! 😉")
                client.user_notification_status = getattr(client, 'user_notification_status', {})
                client.user_notification_status[user_id] = "already_premium_notified"
            return
        
        # Keywords that suggest payment proof
        payment_keywords = [
            'payment', 'paid', 'transaction', 'receipt', 'proof', 'screenshot',
            'done', 'completed', 'success', 'upi', 'gpay', 'phonepe', 'paytm',
            'कर दिया', 'पैसे', 'भेज दिए', 'हो गया', 'प्रीमियम', 'पेमेंट'
        ]
        
        is_payment_related = False
        
        # Check if it's a photo (likely payment screenshot)
        if message.photo:
            is_payment_related = True
        
        # Check if text contains payment-related keywords
        elif message.text:
            text_lower = message.text.lower()
            if any(keyword in text_lower for keyword in payment_keywords):
                is_payment_related = True
            # Check for transaction ID patterns (numbers/alphanumeric)
            elif len(message.text.strip()) > 8 and any(c.isdigit() for c in message.text):
                is_payment_related = True
        
        # Check if it's a document (could be receipt)
        elif message.document:
            if message.document.file_name:
                filename_lower = message.document.file_name.lower()
                if any(keyword in filename_lower for keyword in ['receipt', 'payment', 'transaction']):
                    is_payment_related = True
        
        if is_payment_related:
            # Send notification to bot owner
            owner_notification = (
                f"💰 **New Payment Proof Received**\n\n"
                f"👤 **User:** {user_name} ({username})\n"
                f"🆔 **User ID:** `{user_id}`\n"
                f"📅 **Date:** {time.strftime('%d %b %Y, %H:%M')}\n\n"
                f"**Message Type:** {'Photo' if message.photo else 'Document' if message.document else 'Text'}\n\n"
                f"**To activate premium, use:**\n"
                f"`/addpremium {user_id}`\n\n"
                f"**To reject, ignore this message.**"
            )
            
            try:
                # Forward the actual message to owner
                await message.forward(BOT_OWNER_ID)
                
                # Send notification with user details
                await client.send_message(
                    BOT_OWNER_ID,
                    owner_notification,
                    parse_mode=ParseMode.MARKDOWN
                )
                
                # Confirm receipt to user
                await message.reply_text(
                    "✅ **Payment proof received!**\n\n"
                    "तुम्हारा payment proof मुझे मिल गया है! 📸\n"
                    "अब मैं इसे verify करूँगी और 24 घंटे के अंदर premium activate कर दूँगी!\n\n"
                    "धन्यवाद for your patience! 💖",
                    parse_mode=ParseMode.MARKDOWN
                )
                
            except Exception as e:
                # If forwarding fails, at least log it
                print(f"Failed to forward payment proof from {user_id}: {e}")
                
                # Still confirm to user
                await message.reply_text(
                    "✅ **Payment proof received!**\n\n"
                    "तुम्हारा payment details मुझे मिल गए हैं! मैं जल्दी ही verify करके premium activate कर दूँगी!\n\n"
                    "धन्यवाद! 💖"
                )
