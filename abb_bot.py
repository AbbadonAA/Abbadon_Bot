import os
import requests
# from telegram import ReplyKeyboardMarkup
from telegram.ext import Filters, MessageHandler, Updater, CommandHandler
from dotenv import load_dotenv
import logging
from datetime import datetime as dt

load_dotenv()
secret_token = os.getenv('API_TOKEN')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

CURRENCY_URL = 'https://www.cbr-xml-daily.ru/daily_json.js'


def first_answer(update, context):
    chat = update.effective_chat
    context.bot.send_message(chat_id=chat.id, text='Пока не умею отвечать')


def currency_rate(update, context):
    chat = update.effective_chat
    response = requests.get(CURRENCY_URL).json()
    currencies = response.get('Valute')
    currency = currencies.get(context.args[0])
    name = currency.get('CharCode')
    value = currency.get('Value')
    pr_value = currency.get('Previous')
    var = round(value - pr_value, 3)
    date_str = response.get('Date')[:10]
    correct_date = dt.strptime(date_str, '%Y-%m-%d')
    date = correct_date.strftime('%d.%m.%Y')
    text = (
        f'На {date}: \n'
        f'1 {name} = {value} RUB \n'
        f'Изменение за сутки: {var}'
    )
    context.bot.send_message(
        chat_id=chat.id,
        text=text
    )


def main():
    updater = Updater(token=secret_token)
    updater.dispatcher.add_handler(CommandHandler('currency', currency_rate))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, first_answer))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
