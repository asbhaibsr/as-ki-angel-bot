import random
import time
import asyncio
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from config import STICKER_PROBABILITY, RESPONSE_PROBABILITY, MAX_LEARNING_MEMORY
from database import db

def register_learning_handlers(app, utils):

    @app.on_message(filters.command("learn_stats") & filters.group)
    async def learning_stats(client, message: Message):
        """Show learning statistics for the group."""
        chat_id = message.chat.id
        user_id = message.from_user.id

        # Check if user is admin (for permission)
        try:
            member = await client.get_chat_member(chat_id, user_id)
            if member.status not in ["administrator", "creator"]:
                await message.reply_text("⛔ This command is only for group admins!")
                return
        except Exception as e:
            await message.reply_text(f"❌ Unable to verify admin status: {e}")
            return

        # Get learning data
        group_data = await db.get_group_learning_data(chat_id)

        # Use correct data keys
        learned_phrases = group_data.get('phrases', [])
        learned_stickers = group_data.get('stickers', [])
        response_patterns = group_data.get('response_patterns', {})

        # Calculate statistics
        total_phrases = len(learned_phrases)
        total_stickers = len(learned_stickers)
        total_patterns = len(response_patterns)

        # Get group info (connected_groups collection)
        group_info = await db._run_in_executor(db.connected_groups.find_one, {'_id': chat_id}) or {}
        connected_since = group_info.get('connected_at', 'Recently')
        
        # Ensure connected_since is a string, as it might be stored as time.time() initially
        if isinstance(connected_since, (int, float)):
            connected_since = time.strftime('%d %b %Y', time.localtime(connected_since))

        stats_text = (
            f"📊 **Group Learning Statistics**\n\n"
            f"🏢 **Group:** {message.chat.title}\n"
            f"🤖 **Bot Status:** Active ✅\n\n"
            f"📈 **Learning Progress:**\n"
            f"• Messages Learned: {total_phrases}\n"
            f"• Stickers Learned: {total_stickers}\n"
            f"• Response Patterns: {total_patterns}\n"
            f"• Connected Since: {connected_since}\n\n"
            f"🎯 **Response Breakdown:**\n"
            f"• Short Responses (1-3 words): {len([r for r in learned_phrases if isinstance(r, str) and 1 <= len(r.split()) <= 3])}\n"
            f"• Medium Responses (4-5 words): {len([r for r in learned_phrases if isinstance(r, str) and 4 <= len(r.split()) <= 5])}\n"
            f"• Pattern Triggers: {total_patterns}\n\n"
            f"⚙️ **Bot Behavior:**\n"
            f"• Response Rate: {int(RESPONSE_PROBABILITY * 100)}% (High)\n"
            f"• Learning Mode: Active 🟢\n"
            f"• Memory Usage: {min(total_phrases, MAX_LEARNING_MEMORY)}/{MAX_LEARNING_MEMORY}\n\n"
            "💡 **Tip:** The more you chat, the better I learn your group's style!"
        )

        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh Stats", callback_data='learn_stats')], # Self-refresh
            [InlineKeyboardButton("💎 Premium Features", callback_data='get_premium')]
        ])

        await message.reply_text(stats_text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

    @app.on_message(filters.command("reset_learning") & filters.group)
    async def reset_learning_command(client, message: Message):
        """Reset group learning data (Admin only)."""
        chat_id = message.chat.id
        user_id = message.from_user.id

        # Check if user is admin
        try:
            member = await client.get_chat_member(chat_id, user_id)
            if member.status not in ['administrator', 'creator']:
                await message.reply_text("⛔ This command is only for group admins!")
                return
        except Exception as e:
            await message.reply_text(f"❌ Unable to verify admin status: {e}")
            return

        # Reset learning data using db._run_in_executor
        await db._run_in_executor(db.learning_data.delete_one, {'_id': chat_id})

        reset_text = (
            "🗑️ **Learning Data Reset Complete!**\n\n"
            "✅ All learned responses have been cleared\n"
            "✅ All learned stickers have been removed\n"
            "✅ Group personality has been reset\n\n"
            "🔄 I'll start learning fresh from new conversations!\n"
            "Use `/learn_stats` to monitor the new learning progress."
        )

        await message.reply_text(reset_text, parse_mode=ParseMode.MARKDOWN)

    @app.on_message(filters.group & ~filters.command(""))
    async def learn_and_respond(client, message: Message):
        """Main learning and response handler for group messages."""
        try:
            chat_id = message.chat.id
            user_id = message.from_user.id

            # Skip if it's a service message or bot message
            if message.service or (message.from_user and message.from_user.is_bot):
                return

            # Update user stats using db._run_in_executor
            await db.update_user_stats(user_id, 'group_message')

            # Get group learning data
            group_data = await db.get_group_learning_data(chat_id
