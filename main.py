import asyncio
import sqlite3
import logging
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import TimedOut, BadRequest, RetryAfter
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram Bot credentials
BOT_TOKEN = 'Your-Bot_Token'
GROUP_ID = 'group-id'
DB_FILE = 'db_file'
MEMBERS_TO_ADD_PER_DAY = 15

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


# Initialize database
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS members (id INTEGER PRIMARY KEY)''')
    conn.commit()
    conn.close()


# Function to save group members to the database
async def save_group_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("تابع ذخیره اعضای گروه فراخوانی شد")
    print("تابع ذخیره اعضای گروه فراخوانی شد")
    try:
        chat = await context.bot.get_chat(GROUP_ID)
        members = await context.bot.get_chat_administrators(chat.id)  # get the administrators

        member_ids = [member.user.id for member in members]

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.executemany('INSERT OR IGNORE INTO members (id) VALUES (?)', [(member_id,) for member_id in member_ids])
        conn.commit()
        conn.close()

        for member_id in member_ids:
            print(f"{member_id} آیدی اعضا: ")

        await update.message.reply_text('اعضا در دیتابیس ذخیره شدند')
    except TimedOut:
        await update.message.reply_text('زمان درخواست تمام شد. لطفاً بعداً دوباره امتحان کنید.')
    except BadRequest as e:
        if "CHAT_ADMIN_REQUIRED" in str(e):
            await update.message.reply_text('ربات نیاز به دسترسی ادمین برای گرفتن اعضای گروه دارد.')
        else:
            await update.message.reply_text(f'{e}خطایی رخ داد: ')
        logging.error(f'{e}خطا در ذخیره اعضا: ')
    except RetryAfter as e:
        await asyncio.sleep(e.retry_after)
    except Exception as e:
        await update.message.reply_text(f'{e}خطایی رخ داد: ')
        logging.error(f'{e}خطا در ذخیره اعضا: ')


# Function to add members to the target group using invite link
async def add_members_to_group(context: ContextTypes.DEFAULT_TYPE):
    logging.info("تابع اضافه کردن به گروه فراخوانی شد")
    print("تابع اضافه کردن به گروه فراخوانی شد")

    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('SELECT id FROM members')
        member_ids = [row[0] for row in c.fetchall()]
        conn.close()

        invite_link = await context.bot.create_chat_invite_link(GROUP_ID)
        logging.info(f"لینک دعوت ایجاد شد: {invite_link.invite_link}")
        print(f"لینک دعوت ایجاد شد: {invite_link.invite_link}")

        for i in range(0, len(member_ids), MEMBERS_TO_ADD_PER_DAY):
            members_to_add = member_ids[i:i + MEMBERS_TO_ADD_PER_DAY]
            for member_id in members_to_add:
                try:
                    await context.bot.send_message(member_id, f"لطفاً به گروه بپیوندید: {invite_link.invite_link}")
                    logging.info(f"لینک دعوت به {member_id} ارسال شد.")
                    print(f"لینک دعوت به {member_id} ارسال شد.")
                except Exception as e:
                    logging.error(f" لینک دعوت به {member_id} ارسال نشد: {e}")
                    print(f" لینک دعوت به {member_id} ارسال نشد: {e}")
            time.sleep(86400)  # Sleep for 1 day
    except Exception as e:
        logging.error(f'{e}خطایی رخ داد: ')


# Function to initiate the adding process
async def initiate_adding_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await add_members_to_group(context)
    await update.message.reply_text('شروع به ارسال لینک دعوت به اعضا.')


# Main menu handler
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("ذخیره اعضا", callback_data='ذخیره'),
            InlineKeyboardButton("ادد ممبر", callback_data='ادد کردن به گروه')
        ],
        [
            InlineKeyboardButton("برگشت", callback_data='برگشت')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('یک گزینه را انتخاب کنید:', reply_markup=reply_markup)


# Button handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'ذخیره':
        await save_group_members(query, context)
    elif query.data == 'ادد کردن به گروه':
        await initiate_adding_process(query, context)
    elif query.data == 'برگشت':
        await main_menu(query, context)


# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await main_menu(update, context)


# Main function to start the bot and add handlers
def main():
    init_db()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("save", save_group_members))
    application.add_handler(CommandHandler("add_process", initiate_adding_process))
    application.add_handler(CommandHandler("menu", main_menu))
    application.add_handler(CallbackQueryHandler(button_handler))

    try:
        logging.info("شروع ربات...")
        application.run_polling()
    except TimedOut:
        logging.error(
            'زمان نظرسنجی ربات به پایان رسید. لطفاً اتصال شبکه خود را بررسی کنید یا بعداً دوباره امتحان کنید.')
    except Exception as e:
        logging.error(f'{e}هنگام نظرسنجی ربات خطایی روی داد: ')


if __name__ == '__main__':
    main()

