import logging
import os
from datetime import datetime as dt
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

from exceptions import (EmptyListException, InvalidApiExc, InvalidJsonExc,
                        InvalidResponseExc, InvalidValuteExc)

load_dotenv()
secret_token = os.getenv('API_TOKEN')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

CURRENCY_URL = 'https://www.cbr-xml-daily.ru/daily_json.js'
VALUTE_LIST = [
    'AUD', 'AZN', 'GBP', 'AMD', 'BYN', 'BGN', 'BRL', 'HUF', 'HKD',
    'DKK', 'USD', 'EUR', 'INR', 'KZT', 'CAD', 'KGS', 'CNY', 'MDL',
    'NOK', 'PLN', 'RON', 'XDR', 'SGD', 'TJS', 'TRY', 'TMT', 'UZS',
    'UAH', 'CZK', 'SEK', 'CHF', 'ZAR', 'KRW', 'JPY'
]


def first_answer(update, context):
    chat = update.effective_chat
    context.bot.send_message(chat_id=chat.id, text='Пока не умею отвечать')


def send_message(chat, context, message):
    try:
        context.bot.send_message(chat_id=chat.id, text=message)
    except Exception:
        pass


def get_api_answer():
    try:
        response = requests.get(CURRENCY_URL)
    except Exception as error:
        raise InvalidApiExc(f'Ошибка ответа API: {error}')
    status = response.status_code
    if status != HTTPStatus.OK:
        raise InvalidResponseExc(f'status_code: {status}')
    try:
        return response.json()
    except Exception as error:
        raise InvalidJsonExc(f'Ошибка декодирования JSON: {error}')


def check_data(data, context):
    if 'Valute' not in data:
        raise InvalidApiExc('Некорректный ответ API - Отсутствует Valute')
    if not context.args:
        raise EmptyListException('Не указана валюта')
    # for i in range(len(context.args)):
    charcode = context.args[0]
    if charcode not in VALUTE_LIST:
        raise InvalidValuteExc(
            f'Валюта {charcode} некорректна или не поддерживается')
    try:
        data = data.get('Valute')
    except Exception as error:
        raise InvalidApiExc(f'Не получены данные Valute: {error}')
    if 'CharCode' and 'Value' and 'Previous' not in data.get(charcode):
        raise InvalidApiExc(
            'В ответе API ошибки: CharCode or Value or Previous')
    return data


def corr_date(response):
    if 'Date' not in response:
        raise InvalidApiExc('Некорректный ответ API - Отсутствует Date')
    date_str = response.get('Date')[:10]
    correct_date = dt.strptime(date_str, '%Y-%m-%d')
    date = correct_date.strftime('%d.%m.%Y')
    return date


def parse_valute(currencies, context):
    currency = currencies.get(context.args[0])
    name = currency.get('CharCode')
    value = currency.get('Value')
    pr_value = currency.get('Previous')
    var = round(value - pr_value, 3)
    text = (
        f'1 {name} = {value} RUB \n'
        f'Изменение за сутки: {var}'
    )
    return text


def currency_rate(update, context):
    chat = update.effective_chat
    try:
        response = get_api_answer()
        currencies = check_data(response, context)
        currency = parse_valute(currencies, context)
        date = corr_date(response)
        message = (
            f'На {date}: \n'
            f'{currency}'
        )
        send_message(chat, context, message)
    except Exception as error:
        message = error
        send_message(chat, context, message)
# Не работает Exception!!!

# def currency_rate(update, context):
#     chat = update.effective_chat
#     response = requests.get(CURRENCY_URL).json()
#     currencies = response.get('Valute')
#     currency = currencies.get(context.args[0])
#     name = currency.get('CharCode')
#     value = currency.get('Value')
#     pr_value = currency.get('Previous')
#     var = round(value - pr_value, 3)
#     date_str = response.get('Date')[:10]
#     correct_date = dt.strptime(date_str, '%Y-%m-%d')
#     date = correct_date.strftime('%d.%m.%Y')
#     message = (
#         f'На {date}: \n'
#         f'1 {name} = {value} RUB \n'
#         f'Изменение за сутки: {var}'
#     )
#     context.bot.send_message(
#         chat_id=chat.id,
#         text=message
#     )


def main():
    updater = Updater(token=secret_token)
    updater.dispatcher.add_handler(CommandHandler('currency', currency_rate))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, first_answer))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
