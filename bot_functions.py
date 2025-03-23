from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import json

def load_config():
    with open('config.json', 'r') as file:
        config = json.load(file)
    return config


#update contains info about the incoming message, like chat ID and text
#context holds various info like bot data, user data and arguments
#await says wait for this task to finish before continuing with the code
async def start_command(update: Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! This is a test! I will add instructions later")

async def send_message_to_chat(update:Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message("test")

async def test(bets):
    await print("hello")
    await print(bets)

if __name__ == '__main__':

    config = load_config()
    CHAT_ID = config.get("chat_id")
    TOKEN = config.get("telegram_bot_token")
    BOT_USERNAME = config.get("bot_username")

    #This initializes the bot
    app = Application.builder().token(TOKEN).build()

    #Commands
    app.add_handler(CommandHandler('start', start_command))

    #Bot checks for new messages every 5 seconds
    app.run_polling(poll_interval=5)
