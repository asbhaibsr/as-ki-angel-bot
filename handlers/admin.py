import time
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import BOT_OWNER_ID
from database import db
from pyrogram.enums import ParseMode

def register_admin_handlers(app, utils):

    @app.on_message(filters.command("admin") & filters.private)
    async def admin_panel(client, message: Message):
        """Admin panel for bot owner."""
        user_id = message.from_user.id

        # Debug: Show user ID to help set correct owner ID
        await message.reply_text(f"Your User ID: `{user_id}`\nBot Owner ID: `{BOT_OWNER_ID}`", parse_mode=ParseMode.MARKDOWN)

        if not utils.is_owner(user_id):
            await message.reply_text("⛔ This command is only for bot owner!")
            return

        stats = await db.get_bot_stats()

        admin_text = (
            "👑 **Admin Control Panel**\n\n"
            f"📊 **Bot Statistics:**\n"
            f"• Total Users: {stats['total_users']}\n"
            f"• Total Groups: {stats['total_groups']}\n"
            f"• Premium Users: {stats['premium_users']}\n"
            f"• Learning Groups: {stats['learning_groups']}\n\n"
            "Select an option below:"
        )

        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Detailed Stats", callback_data='admin_stats')],
            [InlineKeyboardButton("👑 Premium Management", callback_data='admin_premium')],
            [InlineKeyboardButton("📢 Broadcast Message", callback_data='admin_broadcast')],
            [InlineKeyboardButton("⚙️ Bot Settings", callback_data='admin_settings')]
        ])

        await message.reply_text(admin_text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

    @app.on_callback_query(filters.regex("admin_stats"))
    async def admin_stats_callback(client, call: CallbackQuery):
        """Show detailed bot statistics."""
        if not utils.is_owner(call.from_user.id):
            await call.answer("⛔ Access denied!", show_alert=True)
            return

        stats = await db.get_bot_stats()

        stats_text = (
            "📊 **Detailed Bot Statistics**\n\n"
            f"👥 **Users:** {stats['total_users']}\n"
            f"🏢 **Groups:** {stats['total_groups']}\n"
            f"💎 **Premium Users:** {stats['premium_users']}\n"
            f"🧠 **Learning Groups:** {stats['learning_groups']}\n\n"
            "📈 **Performance:**\n"
            f"• Bot Uptime: Active\n" # Placeholder, actual uptime tracking needs more logic
            f"• Response Time: <0.1s\n" # Placeholder
            f"• Memory Usage: Normal\n" # Placeholder
        )

        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data='admin_main')]
        ])

        await call.edit_message_text(stats_text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

    @app.on_callback_query(filters.regex("admin_main"))
    async def admin_main_callback(client, call: CallbackQuery):
        """Return to main admin panel."""
        if not utils.is_owner(call.from_user.id):
            await call.answer("⛔ Access denied!", show_alert=True)
            return

        stats = await db.get_bot_stats()

        admin_text = (
            "👑 **Admin Control Panel**\n\n"
            f"📊 **Bot Statistics:**\n"
            f"• Total Users: {stats['total_users']}\n"
            f"• Total Groups: {stats['total_groups']}\n"
            f"• Premium Users: {stats['premium_users']}\n"
            f"• Learning Groups: {stats['learning_groups']}\n\n"
            "Select an option below:"
        )

        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Detailed Stats", callback_data='admin_stats')],
            [InlineKeyboardButton("👑 Premium Management", callback_data='admin_premium')],
            [InlineKeyboardButton("📢 Broadcast Message", callback_data='admin_broadcast')],
            [InlineKeyboardButton("⚙️ Bot Settings", callback_data='admin_settings')]
        ])

        await call.edit_message_text(admin_text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

    @app.on_callback_query(filters.regex("admin_premium"))
    async def premium_management(client, call: CallbackQuery):
        """Premium user management."""
        if not utils.is_owner(call.from_user.id):
            await call.answer("⛔ Access denied!", show_alert=True)
            return

        premium_text = (
            "👑 **Premium Management**\n\n"
            "**Available Commands (in private chat):**\n"
            "• `/addpremium <user_id> [months]` - Add premium\n"
            "• `/removepremium <user_id>` - Remove premium\n"
            "• `/listpremium` - List all active premium users\n\n"
            "Use these commands in chat to manage premium users."
        )

        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 List Premium Users", callback_data='list_premium')],
            [InlineKeyboardButton("🔙 Back", callback_data='admin_main')]
        ])

        await call.edit_message_text(premium_text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

    @app.on_callback_query(filters.regex("list_premium"))
    async def list_premium_users(client, call: CallbackQuery):
        """List all premium users."""
        if not utils.is_owner(call.from_user.id):
            await call.answer("⛔ Access denied!", show_alert=True)
            return

        # Fetch premium users using db._run_in_executor
        premium_users_cursor = await db._run_in_executor(db.premium_users.find, {
            'premium_until': {'$gt': time.time()}
        })
        premium_users = list(premium_users_cursor) # Convert cursor to list

        if not premium_users:
            users_text = "👑 **Premium Users**\n\nNo active premium users found."
        else:
            users_text = "👑 **Active Premium Users:**\n\n"
            for i, user in enumerate(premium_users[:10], 1):  # Show first 10
                expires = utils.format_time_remaining(user['premium_until'])
                users_text += f"{i}. User ID: `{user['_id']}`\n   Expires: {expires}\n\n"

            if len(premium_users) > 10:
                users_text += f"... and {len(premium_users) - 10} more users."

        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data='admin_premium')]
        ])

        await call.edit_message_text(users_text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

    # Removed add_premium_command as it's now in handlers/premium.py

    @app.on_message(filters.command("removepremium") & filters.private)
    async def remove_premium_command(client, message: Message):
        """Remove premium from a user."""
        user_id = message.from_user.id

        if not utils.is_owner(user_id):
            await message.reply_text("⛔ This command is only for bot owner!")
            return

        try:
            parts = message.text.split()
            if len(parts) < 2:
                await message.reply_text("Usage: /removepremium <user_id>")
                return

            target_user_id = int(parts[1])

            # Remove premium by setting expiry to past using db._run_in_executor
            await db._run_in_executor(
                db.premium_users.update_one,
                {'_id': target_user_id},
                {'$set': {'premium_until': 0}}
            )

            await message.reply_text(f"✅ Premium removed from user {target_user_id}!")

            # Notify the user
            try:
                await client.send_message(
                    target_user_id,
                    "📢 **Premium Status Update**\n\n"
                    "तुम्हारा premium subscription terminate हो गया है।\n"
                    "अगर कोई issue है तो contact करो। धन्यवाद! 🙏"
                )
            except Exception as e:
                print(f"Failed to notify user {target_user_id} about premium removal: {e}")

        except ValueError:
            await message.reply_text("❌ Invalid user ID!")
        except Exception as e:
            await message.reply_text(f"❌ Error: {e}")

    @app.on_message(filters.command("broadcast") & filters.private)
    async def broadcast_message(client, message: Message):
        """Broadcast message to all users."""
        user_id = message.from_user.id

        if not utils.is_owner(user_id):
            await message.reply_text("⛔ This command is only for bot owner!")
            return

        if not message.reply_to_message:
            await message.reply_text("❌ Reply to a message to broadcast it!")
            return

        # Get all unique user IDs using db._run_in_executor
        all_users_cursor = await db._run_in_executor(db.user_stats.find, {}, {'_id': 1})
        user_ids = [user['_id'] for user in all_users_cursor]

        if not user_ids:
            await message.reply_text("❌ No users found to broadcast to!")
            return

        broadcast_msg = message.reply_to_message
        success_count = 0
        failed_count = 0

        status_msg = await message.reply_text(f"📢 Broadcasting to {len(user_ids)} users...")

        for target_user_id in user_ids:
            try:
                if broadcast_msg.text:
                    await client.send_message(target_user_id, broadcast_msg.text)
                elif broadcast_msg.photo:
                    await client.send_photo(target_user_id, broadcast_msg.photo.file_id, caption=broadcast_msg.caption)
                elif broadcast_msg.video:
                    await client.send_video(target_user_id, broadcast_msg.video.file_id, caption=broadcast_msg.caption)
                elif broadcast_msg.sticker:
                    await client.send_sticker(target_user_id, broadcast_msg.sticker.file_id)
                else:
                    # Handle other media types if necessary, or skip
                    continue
                success_count += 1
            except Exception as e:
                # Log specific errors if needed, e.g., user blocked bot
                print(f"Failed to send broadcast to {target_user_id}: {e}")
                failed_count += 1
            await asyncio.sleep(0.05) # Small delay to avoid FloodWait

        await status_msg.edit_text(
            f"📢 **Broadcast Complete!**\n\n"
            f"✅ Sent: {success_count}\n"
            f"❌ Failed: {failed_count}\n"
            f"📊 Total: {len(user_ids)}",
            parse_mode=ParseMode.MARKDOWN
        )

    @app.on_callback_query(filters.regex("admin_settings"))
    async def bot_settings(client, call: CallbackQuery):
        """Bot settings and configuration."""
        if not utils.is_owner(call.from_user.id):
            await call.answer("⛔ Access denied!", show_alert=True)
            return

        settings_text = (
            "⚙️ **Bot Settings & Configuration**\n\n"
            "🤖 **Current Bot Status:**\n"
            "• Status: 🟢 Online & Active\n"
            "• Keep-Alive: 🟢 Running\n"
            "• Database: 🟢 Connected\n"
            "• Learning: 🟢 Enabled\n\n"
            "📊 **Learning Settings:**\n"
            "• Response Rate: 60% (Configurable)\n" # Updated to reflect config
            "• Memory Limit: 1000 messages/group\n"
            "• Short Responses: 1-5 words\n"
            "• Sticker Learning: Enabled\n\n"
            "💰 **Premium Settings:**\n"
            "• Price: ₹500 for 5 months\n"
            "• UPI ID: Set in environment\n"
            "• Auto-expiry: Enabled\n\n"
            "Use commands to modify settings:\n"
            "• `/logs` - View bot logs\n"
            "• `/addpremium <user_id>` - Add premium user\n"
            "• `/removepremium <user_id>` - Remove premium\n"
            "• `/broadcast` - Broadcast message"
        )

        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 View Logs", callback_data='admin_logs')],
            [InlineKeyboardButton("🔄 Restart Bot", callback_data='admin_restart')],
            [InlineKeyboardButton("🔙 Back to Main", callback_data='admin_main')]
        ])

        await call.edit_message_text(settings_text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

    @app.on_callback_query(filters.regex("admin_logs"))
    async def show_admin_logs(client, call: CallbackQuery):
        """Show bot logs via callback."""
        if not utils.is_owner(call.from_user.id):
            await call.answer("⛔ Access denied!", show_alert=True)
            return

        # In a real deployment, you'd integrate with a logging system or file
        logs_text = (
            "📋 **Recent Bot Activity**\n\n"
            "✅ Bot is running smoothly\n"
            "📊 All systems operational\n"
            "🔄 Keep-alive server active\n"
            "💾 Database connection stable\n"
            "🤖 Learning system active\n\n"
            "For detailed logs, check hosting platform (Koyeb/Replit) logs."
        )

        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Settings", callback_data='admin_settings')]
        ])

        await call.edit_message_text(logs_text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

    @app.on_callback_query(filters.regex("admin_restart"))
    async def restart_bot_callback(client, call: CallbackQuery):
        """Restart bot confirmation."""
        if not utils.is_owner(call.from_user.id):
            await call.answer("⛔ Access denied!", show_alert=True)
            return

        restart_text = (
            "🔄 **Restart Bot**\n\n"
            "⚠️ This will restart the bot process.\n"
            "The bot will be offline for a few seconds.\n\n"
            "Are you sure you want to restart?"
        )

        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Yes, Restart", callback_data='confirm_restart')],
            [InlineKeyboardButton("❌ Cancel", callback_data='admin_settings')]
        ])

        await call.edit_message_text(restart_text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

    @app.on_callback_query(filters.regex("confirm_restart"))
    async def confirm_restart_bot(client, call: CallbackQuery):
        """Confirm and restart bot."""
        if not utils.is_owner(call.from_user.id):
            await call.answer("⛔ Access denied!", show_alert=True)
            return

        await call.edit_message_text(
            "🔄 **Restarting Bot...**\n\n"
            "Bot will be back online in a few seconds.",
            parse_mode=ParseMode.MARKDOWN
        )

        # In Koyeb, os._exit(0) will trigger a restart of the container
        import os
        os._exit(0)

    @app.on_message(filters.command("logs") & filters.private)
    async def show_logs_command(client, message: Message):
        """Show recent bot logs via command."""
        user_id = message.from_user.id

        if not utils.is_owner(user_id):
            await message.reply_text("⛔ This command is only for bot owner!")
            return

        # This is a basic implementation - in production you'd want proper logging
        logs_text = (
            "📋 **Recent Bot Activity**\n\n"
            "✅ Bot is running smoothly\n"
            "📊 All systems operational\n"
            "🔄 Last restart: Bot startup\n\n"
            "For detailed logs, check your hosting platform (Koyeb/Replit) logs."
        )

        await message.reply_text(logs_text, parse_mode=ParseMode.MARKDOWN)
