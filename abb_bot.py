import os
# import requests
# from telegram import ReplyKeyboardMarkup
from telegram.ext import Filters, MessageHandler, Updater
# CommandHandler
from dotenv import load_dotenv

load_dotenv()
secret_token = os.getenv('API_TOKEN')


def first_answer(update, context):
    chat = update.effective_chat
    context.bot.send_message(chat_id=chat.id, text='Салют, я работаю')


def main():
    updater = Updater(token=secret_token)
    updater.dispatcher.add_handler(MessageHandler(Filters.text, first_answer))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
