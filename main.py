import os

from dotenv import load_dotenv
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

from kitty import cat_image
from random_answer import first_answer
from valutes.valutes import all_valutes, currency_rate

path = '/home/abbadon/dev/Abbadon_Bot/infra/.env'
load_dotenv(path)
secret_token = os.getenv('API_TOKEN')
# secret_token = os.getenv('API_TEST')


def main():
    updater = Updater(token=secret_token)
    updater.dispatcher.add_handler(CommandHandler('valutes', all_valutes))
    updater.dispatcher.add_handler(
        MessageHandler(Filters.regex(r'\b[мякМЯК]{3}\b'), cat_image))
    updater.dispatcher.add_handler(
        CommandHandler('currency', currency_rate))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, first_answer))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
