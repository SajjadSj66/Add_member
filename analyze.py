from telegram import Update, ChatMember, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler

# Replace with your actual bot token
bot_token = 'bot-token'
group_id = 'group-id'  # Replace with the target group username or ID

print("ok")


async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("شروع آنالیز", callback_data='analyze')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('سلام! برای شروع آنالیز گروه، روی دکمه زیر کلیک کنید.', reply_markup=reply_markup)


async def analyze_group(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    chat = query.message.chat

    if chat.type in ['group', 'supergroup']:
        try:
            # Get the number of members in the group
            members_count = await context.bot.get_chat_member_count(chat.id)
            online_count = 0
            real_members = 0
            fake_members = 0

            # Fetch and analyze each member
            async for member in context.bot.get_chat_administrators(chat.id):
                user = member.user
                member_status = await context.bot.get_chat_member(chat.id, user.id)

                # Check online status
                if member_status.status == ChatMember.STATUS_ONLINE:
                    online_count += 1

                # Heuristic for fake members
                if not user.photo or len(user.bio or '') < 10:
                    fake_members += 1
                else:
                    real_members += 1

            fake_members = max(0, members_count - real_members)  # Ensure non-negative

            await query.message.reply_text(
                f'تحلیل گروه:\n'
                f'تعداد کل اعضا: {members_count}\n'
                f'اعضای واقعی: {real_members}\n'
                f'اعضای تقلبی: {fake_members}\n'
                f'اعضای آنلاین: {online_count}'
            )
        except Exception as e:
            await query.message.reply_text(f'خطا: {str(e)}')
    else:
        await query.message.reply_text('این فرمان فقط در گروه‌ها قابل استفاده است.')


def main() -> None:
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(bot_token).build()

    # Add the command handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(analyze_group, pattern='analyze'))

    # Run the bot
    application.run_polling()


print("ok")
if __name__ == '__main__':
    main()
