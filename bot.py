from src.negative_sentiment_analyzer import NegativeSentimentAnalyzer
from src.env import Env
from telegram import Update
from telegram.ext import MessageHandler, filters, ApplicationBuilder, ContextTypes

from dotenv import load_dotenv
import os
import logging
logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S', level=logging.INFO)


load_dotenv()


analyzer = NegativeSentimentAnalyzer(os.getenv("OPENAI_API_KEY"))

BAN_STICKER_SETS = [
    "Lustful",
    "IgnoranzaRegna",
    "vsrpron",
    "CryptoCurvepack",
    "Tresxxx",
    "sexNfun",
    "rbkp01",
    "johnnysinsbrazzers",
    "PornActress",
    "James_Deen_stickers",
    "BrotherhoodBald",
    "Sexting",
    "MyDick",
    "Genitalia_stickers",
    "GayRainbowStickers",
    "Cnaked",
    "Hottie",
    "Pooorno",
    "Porn87",
    "xxxpornxxx",
    "pornguys",
    "Pornstars1",
    "Thomascuck"
]


# format {chat_id : [thread_ids]}
# Single source of truth: determines which chats to moderate and where to send reminders
if Env.ENVIRON == "prod":
    THREADS_TO_MODERATE = {
        -1001622898322: [158009, 1165021, 238474, 1723216, 1]
    }
    REMINDERS_TO_SEND = [
        # --- GOLD CHAT (Thread 158009) ---
        # Message 1: Sends every 8 hours (3x a day), starting immediately
        {
            "chat_id": -1001622898322,
            "threads": [158009],
            "text": "Trade with up to 400.000$ in capital. Instantly today. Www.ertfundedfred.com 👈🏻",
            "interval_seconds": 28800,
            "first_seconds": 0
        },
        # Message 2: Sends every 8 hours (3x a day), starting after 4 hours (14400 seconds)
        {
            "chat_id": -1001622898322,
            "threads": [158009],
            "text": "Out of capital? Get a 100% TRADEABLE deposit bonus up until 5000$ today. Sign up here💰\n\n👉🏻 https://fred-frost.com/bullwave/ 👈🏻",
            "interval_seconds": 28800,
            "first_seconds": 14400
        },

        # --- OTHER CHATS (All other threads) ---
        # Message 1: Sends every 24 hours (1x a day), starting immediately
        {
            "chat_id": -1001622898322,
            "threads": [238474, 1, 1165021, 1267563],
            "text": "Trade with up to 400.000$ in capital. Instantly today. Www.ertfundedfred.com 👈🏻",
            "interval_seconds": 86400,
            "first_seconds": 0
        },
        # Message 2: Sends every 24 hours (1x a day), starting after 12 hours (43200 seconds)
        {
            "chat_id": -1001622898322,
            "threads": [238474, 1, 1165021, 1267563],
            "text": "Out of capital? Get a 100% TRADEABLE deposit bonus up until 5000$ today. Sign up here💰\n\n👉🏻 https://fred-frost.com/bullwave/ 👈🏻",
            "interval_seconds": 86400,
            "first_seconds": 43200
        }
    ]
else:
    THREADS_TO_MODERATE = {
        -1001843081678: [213]
    }
    REMINDERS_TO_SEND = [
        # Message 1: Sends every 60 seconds, starting immediately
        {
            "chat_id": -1001843081678,
            "threads": [213],
            "text": "Trade with up to 400.000$ in capital. Instantly today. Www.ertfundedfred.com 👈🏻",
            "interval_seconds": 60,
            "first_seconds": 0
        },
        # Message 2: Sends every 60 seconds, starting after 30 seconds
        {
            "chat_id": -1001843081678,
            "threads": [213],
            "text": "Out of capital? Get a 100% TRADEABLE deposit bonus up until 5000$ today. Sign up here💰\n\n👉🏻 https://fred-frost.com/bullwave/ 👈🏻",
            "interval_seconds": 60,
            "first_seconds": 30
        }
    ]


chat_admins = {}


async def delete_negative_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = update.message
    if message is None:
        message = update.edited_message
    if message is None:
        return

    message_text = message.text
    if message_text is None:
        return

    chat_id = message.chat_id

    # Delete command messages (starting with "/" or containing "/click" or containing any command like "/word")
    has_command = False
    for word in message_text.split():
        if word.startswith("/"):
            has_command = True
            break
    if has_command:
        logging.info(f"Deleting command/click message \"{message_text}\"")
        await context.bot.delete_message(chat_id, message.message_id)
        return

    user_id = message.from_user.id
    thread_id = message.message_thread_id

    # Only moderate chats defined in THREADS_TO_MODERATE
    if chat_id not in THREADS_TO_MODERATE:
        return
    if thread_id not in THREADS_TO_MODERATE[chat_id]:
        return

    logging.info(
        f"Message {message_text} with chat_id {chat_id} and thread_id {thread_id}")

    if chat_id not in chat_admins:
        try:
            admins = await context.bot.get_chat_administrators(chat_id)
            chat_admins[chat_id] = [admin.user.id for admin in admins]
        except:
            chat_admins[chat_id] = []

    # Skip admin moderation unless DEBUG is enabled
    if not Env.DEBUG and user_id in chat_admins[chat_id]:
        return

    if analyzer.is_negative(message_text):
        logging.info(f"Deleting negative message \"{message_text}\"")
        await context.bot.delete_message(chat_id, message.message_id)


async def delete_negative_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if message is None:
        return

    chat_id = message.chat_id

    # Only moderate chats defined in THREADS_TO_MODERATE
    if chat_id not in THREADS_TO_MODERATE:
        return

    sticker = message.sticker
    if sticker and sticker.set_name in BAN_STICKER_SETS:
        await context.bot.delete_message(
            message.chat_id, message.message_id)
        return

    # Check for porn gifs (animations)
    animation = message.animation
    if animation:
        banned_gif_keywords = ["porn", "sex", "xxx", "nsfw", "nude", "naked", "hottie", "boobs", "dick", "pussy", "cunt", "anal", "blowjob", "erotic"]
        filename = (animation.file_name or "").lower()
        caption = (message.caption or "").lower()
        if any(kw in filename or kw in caption for kw in banned_gif_keywords):
            logging.info(f"Deleting porn gif: filename={filename}, caption={caption}")
            await context.bot.delete_message(message.chat_id, message.message_id)
            return


async def send_reminder_message(context: ContextTypes.DEFAULT_TYPE):
    text = context.job.data["text"]
    await context.bot.send_message(
        chat_id=context.job.data["chat_id"], message_thread_id=context.job.data["thread_id"], text=text)


def main():

    app = ApplicationBuilder().token(Env.TELEGRAM_MODERATOR_BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT, delete_negative_messages))

    app.add_handler(MessageHandler(
        filters.ATTACHMENT, delete_negative_sticker))

    j = app.job_queue
    for reminder in REMINDERS_TO_SEND:
        seconds = reminder.get("first_seconds", get_value(0, 57600))
        chat_id = reminder["chat_id"]
        text = reminder["text"]
        for thread_id in reminder["threads"]:
            interval = reminder.get("interval_seconds", get_value(30, 86400))
            j.run_repeating(
                send_reminder_message,
                interval,
                seconds,
                data={
                    "chat_id": chat_id,
                    "thread_id": thread_id,
                    "text": text
                }
            )
            seconds += get_value(2, 5)

    logging.info("Running polling")
    app.run_polling()


def get_value(dev_value, prod_value):
    if Env.ENVIRON == "prod":
        return prod_value
    else:
        return dev_value


if __name__ == '__main__':
    main()
