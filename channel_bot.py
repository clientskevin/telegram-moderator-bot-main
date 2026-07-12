from src.env import Env

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
)
from dotenv import load_dotenv
import os
import logging
import time
from urllib.parse import quote


logging.basicConfig(
    format="%(asctime)s %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    level=logging.INFO,
)

load_dotenv()

# Whitelist of allowed users (user IDs)
# Add your Telegram user ID here. You can get it by messaging @userinfobot on Telegram
if Env.ENVIRON == "prod":
    ALLOWED_USERS = [
        # Add allowed user IDs here, e.g.:
        1096814135,
        1047563173,
    ]
    ALLOWED_CHANNELS = {
        -1001204626673: "fredtradingdaily",
        -1003666401826: "fredtradinguk"
        # Add more channels here: channel_id: "Channel Name"
    }
else:
    ALLOWED_USERS = [
        8592300595,
        1047563173
    ]
    ALLOWED_CHANNELS = {
        -1003692961040: "Fred Test Channel",
        # Add more channels here: channel_id: "Channel Name"
    }


def is_authorized_user(update: Update) -> bool:
    """Check if the user is authorized to use the bot"""
    if not ALLOWED_USERS:
        # If no users specified, allow all (for initial setup)
        return True
    return update.effective_user.id in ALLOWED_USERS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    if not is_authorized_user(update):
        return

    if update.message:
        await update.message.reply_text(
            "👋 <b>Welcome to Channel Poster Bot!</b>\n\n"
            "📢 <b>Send messages to your channels with ease</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📝 <b>How to Send Messages:</b>\n\n"
            "1️⃣ Send your complete message to the bot\n"
            "   (text, media with caption, chat links, etc.)\n\n"
            "2️⃣ Reply to that message with: <code>/send [buttons]</code>\n\n"
            "3️⃣ Select a channel from the options\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔘 <b>Button Format:</b>\n"
            "<code>Button Text | Button URL</code>\n\n"
            "Multiple buttons: Separate with commas\n\n"
            "💡 <b>Examples:</b>\n"
            "• <code>/send</code>\n"
            "• <code>/send Contact Us | https://t.me/username</code>\n"
            "• <code>/send Join Channel | https://t.me/channel, Contact | https://t.me/username</code>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📋 <b>Supported Media:</b>\n"
            "🖼️ Photo  📹 Video  📄 Document  🎵 Audio\n"
            "🎤 Voice  🎬 Animation (GIF)  📹 Video Note\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚡ <b>Other Commands:</b>\n\n"
            "🔗 <b>/generate_link</b> <code>&lt;message&gt;</code>\n"
            "   Generate a Telegram link to chat with you\n"
            "   Example: <code>/generate_link Hello! I need help.</code>\n\n"
            "📋 <b>/list</b>\n"
            "   See all available channels\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "✨ Ready to post? Send your message and reply with <code>/send</code>!",
            parse_mode="HTML"
        )


async def list_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all allowed channels"""
    if not is_authorized_user(update):
        return

    if not update.message:
        return

    if not ALLOWED_CHANNELS:
        await update.message.reply_text("No channels configured.")
        return

    channels_list = "\n".join(
        [f"• {name} (ID: {chat_id})" for chat_id,
         name in ALLOWED_CHANNELS.items()]
    )
    await update.message.reply_text(f"Available channels:\n\n{channels_list}")


async def generate_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate a Telegram link to chat with the user with a pretyped message"""
    if not is_authorized_user(update):
        return

    if not update.message:
        return

    # Check if message text provided
    if not context.args:
        await update.message.reply_text(
            "Usage: /generate_link <message>\n\n"
            "Example:\n"
            '/generate_link "Hello! How can I help you?"'
        )
        return

    # Get the pretyped message
    pretyped_message = " ".join(context.args)

    # Get user's username
    user = update.message.from_user
    username = user.username

    if not username:
        await update.message.reply_text(
            "❌ You need to have a username set in Telegram to generate a link.\n"
            "Set your username in Telegram Settings > Username"
        )
        return

    # Generate the Telegram link
    # Format: https://t.me/username?text=message
    # Use quote instead of quote_plus to encode spaces as %20 instead of +
    encoded_message = quote(pretyped_message)
    telegram_link = f"https://t.me/{username}?text={encoded_message}"

    await update.message.reply_text(
        f"🔗 Your Telegram link:\n\n`{telegram_link}`",
        parse_mode="Markdown"
    )


async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message to a channel - user sends complete message first, then replies with /send"""
    if not is_authorized_user(update):
        return

    if not update.message:
        return

    # Must be a reply to a message
    replied_message = update.message.reply_to_message
    if not replied_message:
        await update.message.reply_text(
            "❌ Please reply to a message with /send\n\n"
            "How to use:\n"
            "1. Send your complete message to the bot (text, media with caption, etc.)\n"
            "2. Reply to that message with: /send [buttons]\n"
            "3. Select a channel from the options\n\n"
            "Use /list to see available channels."
        )
        return

    # Parse buttons from command arguments if provided
    buttons_from_command = None
    if context.args:
        buttons_text = " ".join(context.args)
        buttons_from_command = parse_buttons(buttons_text)

    # Extract and store message data for when channel is selected
    message_data = extract_message_data(replied_message, buttons_from_command)

    # Store in user_data with a unique key
    message_key = f"msg_{int(time.time())}_{update.message.message_id}"
    context.user_data[message_key] = message_data

    # Create inline keyboard with channel options
    keyboard = []
    for channel_id, channel_name in ALLOWED_CHANNELS.items():
        callback_data = f"send_{message_key}_{channel_id}"
        keyboard.append([InlineKeyboardButton(
            channel_name, callback_data=callback_data)])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Select a channel to send the message to:",
        reply_markup=reply_markup,
    )


def parse_buttons(buttons_text: str):
    """Parse buttons from text in format 'Button Text | URL' or 'Text | URL, Text2 | URL2'"""
    buttons = []

    # Split by comma to get individual buttons
    button_strings = buttons_text.split(",")

    for button_str in button_strings:
        button_str = button_str.strip()
        # Remove quotes if present
        if button_str.startswith('"') or button_str.startswith("'"):
            button_str = button_str[1:]
        if button_str.endswith('"') or button_str.endswith("'"):
            button_str = button_str[:-1]

        # Split by pipe to get text and URL
        if "|" in button_str:
            parts = button_str.split("|", 1)
            text = parts[0].strip()
            url = parts[1].strip()

            if text and url:
                buttons.append({"text": text, "url": url})
        else:
            # If no pipe, treat entire string as text with empty callback_data
            if button_str:
                buttons.append({"text": button_str, "callback_data": ""})

    return buttons if buttons else None


def extract_message_data(message, buttons_from_command=None):
    """Extract all data from a message for later sending"""
    data = {
        "has_media": False,
        "media_type": None,
        "media_file_id": None,
        "caption": message.caption or message.text,
        "reply_markup": message.reply_markup,
    }

    # Check for different media types
    if message.photo:
        data["has_media"] = True
        data["media_type"] = "photo"
        data["media_file_id"] = message.photo[-1].file_id
    elif message.video:
        data["has_media"] = True
        data["media_type"] = "video"
        data["media_file_id"] = message.video.file_id
    elif message.document:
        data["has_media"] = True
        data["media_type"] = "document"
        data["media_file_id"] = message.document.file_id
    elif message.audio:
        data["has_media"] = True
        data["media_type"] = "audio"
        data["media_file_id"] = message.audio.file_id
    elif message.voice:
        data["has_media"] = True
        data["media_type"] = "voice"
        data["media_file_id"] = message.voice.file_id
    elif message.animation:
        data["has_media"] = True
        data["media_type"] = "animation"
        data["media_file_id"] = message.animation.file_id
    elif message.video_note:
        data["has_media"] = True
        data["media_type"] = "video_note"
        data["media_file_id"] = message.video_note.file_id

    # Override with buttons from command if provided
    if buttons_from_command:
        keyboard = []
        for button in buttons_from_command:
            if "text" in button and "url" in button:
                keyboard.append([InlineKeyboardButton(
                    button["text"], url=button["url"])])
            elif "text" in button and "callback_data" in button:
                keyboard.append([InlineKeyboardButton(
                    button["text"], callback_data=button["callback_data"])])
        if keyboard:
            data["reply_markup"] = InlineKeyboardMarkup(keyboard)

    return data


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button callbacks - both channel selection and message buttons"""
    if not is_authorized_user(update):
        return

    query = update.callback_query
    if not query:
        return

    # Check if this is a channel selection callback
    if query.data.startswith("send_"):
        await handle_channel_selection(query, context)
    else:
        # Regular button callback from sent messages
        await query.answer(f"Button clicked: {query.data}")


async def handle_channel_selection(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle when user selects a channel to send message to"""
    await query.answer("Sending message...")

    # Parse callback data: send_<message_key>_<channel_id>
    # Example: send_msg_1234567890_123_456789
    # We need to extract message_key (msg_1234567890_123) and channel_id (456789)

    if not query.data.startswith("send_"):
        await query.edit_message_text("❌ Invalid callback data format.")
        return

    # Remove "send_" prefix
    data_without_prefix = query.data[5:]  # Remove "send_"

    # Split by "_" to get all parts
    parts = data_without_prefix.split("_")

    if len(parts) < 2:
        await query.edit_message_text("❌ Invalid channel selection.")
        return

    # Last part is the channel_id
    try:
        channel_id = int(parts[-1])
    except ValueError:
        await query.edit_message_text("❌ Invalid channel ID.")
        return

    # Everything before the last part is the message_key
    message_key = "_".join(parts[:-1])

    # Get stored message data
    message_data = context.user_data.get(message_key)
    if not message_data:
        await query.edit_message_text("❌ Message data not found. Please try again.")
        return

    # Check if channel is whitelisted
    if channel_id not in ALLOWED_CHANNELS:
        await query.edit_message_text("❌ Channel not in whitelist.")
        return

    # Send the message
    try:
        sent_message = await send_message_to_channel(
            context.bot, channel_id, message_data
        )

        channel_name = ALLOWED_CHANNELS.get(channel_id, str(channel_id))
        await query.edit_message_text(
            f"✅ Message sent successfully to {channel_name}!"
        )

        # Clean up stored data
        del context.user_data[message_key]

        logging.info(
            f"Sent {message_data['media_type'] if message_data['has_media'] else 'text'} message to channel {channel_id} ({channel_name})"
        )
    except Exception as e:
        error_msg = str(e)
        await query.edit_message_text(f"❌ Failed to send message: {error_msg}")
        logging.error(
            f"Failed to send message to channel {channel_id}: {error_msg}")


async def send_message_to_channel(bot, channel_id, message_data):
    """Send a message to a channel based on stored message data"""
    has_media = message_data["has_media"]
    media_type = message_data["media_type"]
    media_file_id = message_data["media_file_id"]
    caption = message_data["caption"]
    reply_markup = message_data["reply_markup"]

    if has_media:
        if media_type == "photo":
            return await bot.send_photo(
                chat_id=channel_id,
                photo=media_file_id,
                caption=caption,
                reply_markup=reply_markup,
            )
        elif media_type == "video":
            return await bot.send_video(
                chat_id=channel_id,
                video=media_file_id,
                caption=caption,
                reply_markup=reply_markup,
            )
        elif media_type == "document":
            return await bot.send_document(
                chat_id=channel_id,
                document=media_file_id,
                caption=caption,
                reply_markup=reply_markup,
            )
        elif media_type == "audio":
            return await bot.send_audio(
                chat_id=channel_id,
                audio=media_file_id,
                caption=caption,
                reply_markup=reply_markup,
            )
        elif media_type == "voice":
            return await bot.send_voice(
                chat_id=channel_id,
                voice=media_file_id,
                caption=caption,
                reply_markup=reply_markup,
            )
        elif media_type == "animation":
            return await bot.send_animation(
                chat_id=channel_id,
                animation=media_file_id,
                caption=caption,
                reply_markup=reply_markup,
            )
        elif media_type == "video_note":
            return await bot.send_video_note(
                chat_id=channel_id,
                video_note=media_file_id,
                reply_markup=reply_markup,
            )
    else:
        if not caption:
            raise ValueError("No text content in message")
        return await bot.send_message(
            chat_id=channel_id,
            text=caption,
            reply_markup=reply_markup,
        )


def main():
    app = ApplicationBuilder().token(Env.TELEGRAM_CHANNEL_POSTER_BOT_TOKEN).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_channels))
    app.add_handler(CommandHandler("send", send_message))
    app.add_handler(CommandHandler("generate_link", generate_link))
    app.add_handler(CallbackQueryHandler(button_callback))

    logging.info("Channel bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
