import os

from dotenv import load_dotenv
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

from valutes_cb import all_valutes, currency_rate_cb
from random_answer import first_answer

load_dotenv()
secret_token = os.getenv('API_TOKEN')


def main():
    updater = Updater(token=secret_token)
    updater.dispatcher.add_handler(CommandHandler('valutes', all_valutes))
    updater.dispatcher.add_handler(
        CommandHandler('currency', currency_rate_cb))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, first_answer))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
