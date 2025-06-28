import random
import time
import asyncio
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from config import STICKER_PROBABILITY, RESPONSE_PROBABILITY, MAX_LEARNING_MEMORY, MIN_WORD_LENGTH
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
            group_data = await db.get_group_learning_data(chat_id)

            # Learn from the message
            await learn_from_message(message, group_data, utils)

            # Decide if bot should respond
            if utils.should_respond(message): # Modified to only pass message
                # Generate response in background for speed
                asyncio.create_task(generate_response(client, message, group_data, utils))

            # Save updated learning data
            await db.save_group_learning_data(chat_id, group_data)

        except Exception as e:
            print(f"Error in learn_and_respond: {e}")

    async def learn_from_message(message: Message, group_data, utils):
        """Learn from a message and update group data."""
        try:
            # Ensure data structures exist (deques are handled by get_group_learning_data)
            # No need to re-initialize here if get_group_learning_data ensures them.
                
            # Learn text patterns
            if message.text:
                cleaned_text = utils.clean_text_for_learning(message.text)
                if cleaned_text:
                    group_data['phrases'].append(cleaned_text)

                    # Update response patterns
                    words = cleaned_text.lower().split()
                    for word in words:
                        if len(word) >= MIN_WORD_LENGTH:  # Use MIN_WORD_LENGTH from config
                            if word not in group_data['response_patterns']:
                                group_data['response_patterns'][word] = []

                            # Store potential responses from this message
                            short_response = utils.extract_short_response(cleaned_text)
                            if short_response and short_response not in group_data['response_patterns'][word]:
                                group_data['response_patterns'][word].append(short_response)

            # Learn stickers
            if message.sticker:
                sticker_id = message.sticker.file_id
                # Check if it's a valid sticker (not an animated emoji etc.)
                if sticker_id and message.sticker.is_animated is False and message.sticker.is_video is False:
                    if sticker_id not in group_data['stickers']:
                        group_data['stickers'].append(sticker_id)

            # Learn from replied messages (context learning)
            if message.reply_to_message and message.reply_to_message.text and message.text:
                original_text = utils.clean_text_for_learning(message.reply_to_message.text)
                response_text = utils.clean_text_for_learning(message.text)

                if original_text and response_text:
                    # Create context patterns
                    original_words = original_text.lower().split()
                    response_short = utils.extract_short_response(response_text)

                    if response_short:
                        for word in original_words:
                            if len(word) >= MIN_WORD_LENGTH: # Use MIN_WORD_LENGTH from config
                                if word not in group_data['response_patterns']:
                                    group_data['response_patterns'][word] = []

                                if response_short not in group_data['response_patterns'][word]:
                                    group_data['response_patterns'][word].append(response_short)

        except Exception as e:
            print(f"Error in learn_from_message: {e}")

    async def generate_response(client, message: Message, group_data, utils):
        """Generate and send a response based on learned patterns."""
        try:
            # Decide between sticker and text response
            if group_data.get('stickers') and random.random() < STICKER_PROBABILITY:
                # Send a random learned sticker
                sticker_id = random.choice(list(group_data['stickers']))
                try:
                    await client.send_sticker(message.chat.id, sticker_id)
                    return
                except Exception as e:
                    print(f"Failed to send sticker {sticker_id}: {e}")
                    # Fallback to text if sticker sending fails

            # Generate text response
            response_text = await generate_text_response(message, group_data, utils)

            if response_text:
                # Sometimes reply to the message, sometimes just send
                if random.random() < 0.6:  # 60% chance to reply
                    await message.reply_text(response_text)
                else:
                    await client.send_message(message.chat.id, response_text)

        except Exception as e:
            print(f"Error in generate_response: {e}")

    async def generate_text_response(message: Message, group_data, utils):
        """Generate a text response based on learned patterns."""
        try:
            if not message.text:
                return None

            text = message.text.lower()
            words = text.split()

            # Look for matching patterns
            possible_responses = []

            for word in words:
                if word in group_data['response_patterns']:
                    possible_responses.extend(group_data['response_patterns'][word])

            # If we have learned responses, use them
            if possible_responses:
                return random.choice(possible_responses)

            # Fallback to generic responses based on message content
            return get_fallback_response(text)

        except Exception as e:
            print(f"Error in generate_text_response: {e}")
            return None

    def get_fallback_response(text):
        """Generate fallback responses for common patterns."""
        text = text.lower()

        # Question patterns
        if any(word in text for word in ['क्या', 'कैसे', 'कब', 'कहाँ', 'क्यों', 'what', 'how', 'when', 'where', 'why']):
            return random.choice(['पता नहीं', 'शायद', 'हो सकता है', 'maybe', 'could be'])

        # Greeting patterns
        if any(word in text for word in ['हाय', 'hello', 'hi', 'hey', 'नमस्ते']):
            return random.choice(['हाय!', 'hello!', 'हेलो!', 'नमस्ते!', 'hi!'])

        # Positive patterns
        if any(word in text for word in ['अच्छा', 'बढ़िया', 'शानदार', 'good', 'great', 'awesome', 'nice']):
            return random.choice(['वाह!', 'great!', 'nice!', '👍', 'awesome!'])

        # Negative patterns
        if any(word in text for word in ['बुरा', 'गलत', 'खराब', 'bad', 'wrong', 'terrible']):
            return random.choice(['ओह नो!', 'oh no!', 'sad!', '😢', 'that sucks'])

        # Thanks patterns
        if any(word in text for word in ['धन्यवाद', 'thank', 'thanks', 'शुक्रिया']):
            return random.choice(['welcome!', 'no problem!', 'कोई बात नहीं!', '😊'])

        # Laugh patterns
        if any(word in text for word in ['हाहा', 'lol', 'haha', '😂', '🤣']):
            return random.choice(['हाहा!', 'lol!', '😂', '🤣', 'funny!'])

        # Default responses
        generic_responses = [
            'हम्म', 'okay', 'अच्छा', 'right', 'cool', 'nice', 'सही है', 'हाँ', 'नहीं',
            '👍', '👌', '😊', 'maybe', 'शायद', 'हो सकता है'
        ]

        return random.choice(generic_responses)
