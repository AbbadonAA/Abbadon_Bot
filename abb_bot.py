import logging
import os
import sys
from datetime import datetime as dt
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

from exceptions import (EmptyListException, InvalidApiExc, InvalidJsonExc,
                        InvalidResponseExc, InvalidValuteExc)

load_dotenv()
secret_token = os.getenv('API_TOKEN')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

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
    """Отправка сообщения."""
    try:
        context.bot.send_message(chat_id=chat.id, text=message)
        logger.info(f'Бот отпавил сообщение: {message}')
    except Exception as error:
        logger.error(f'Ошибка отправки сообщения: {error}')


def get_api_answer():
    """Проверка успешности запроса к API."""
    try:
        response = requests.get(CURRENCY_URL)
    except Exception as error:
        raise InvalidApiExc(f'Ошибка ответа API: {error}')
    status = response.status_code
    if status != HTTPStatus.OK:
        logger.error(f'Ответ API: {status}')
        raise InvalidResponseExc(f'status_code: {status}')
    try:
        return response.json()
    except Exception as error:
        raise InvalidJsonExc(f'Ошибка декодирования JSON: {error}')


def all_valutes(update, context):
    chat = update.effective_chat
    response = get_api_answer()
    try:
        valutes = response.get('Valute').keys()
    except Exception as error:
        logger.error(f'Получение ключей Valute: {error}')
        raise InvalidApiExc(f'Некорректный ответ API - {error}')
    valutes_name = response.get('Valute')
    message_list = []
    for valute in valutes:
        try:
            name = valutes_name.get(valute).get('Name')
        except Exception as error:
            logger.error(f'Не получен Name валюты: {error}')
            raise InvalidApiExc(f'Проблемы с получением Name: {error}')
        message_list.append(f'{valute} - {name}')
    message = '\n'.join(message_list)
    send_message(chat, context, message)


def check_data(data, context):
    """Проверка корректности ответа API."""
    if 'Valute' not in data:
        raise InvalidApiExc('Некорректный ответ API - Отсутствует Valute')
    if not context:
        raise EmptyListException('Не указана валюта')
    charcode = context
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
    """Перевод даты в нужный формат."""
    if 'Date' not in response:
        raise InvalidApiExc('Некорректный ответ API - Отсутствует Date')
    date_str = response.get('Date')[:10]
    correct_date = dt.strptime(date_str, '%Y-%m-%d')
    date = correct_date.strftime('%d.%m.%Y')
    return date


def parse_valute(currencies, context):
    """Получение курса валюты и подготовка сообщения."""
    currency = currencies.get(context)
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
    """Основная логика работы блока валюты ЦБ."""
    chat = update.effective_chat
    for i in range(len(context.args)):
        try:
            logger.debug('Отправка запроса к API')
            response = get_api_answer()
            currencies = check_data(response, context.args[i])
            currency = parse_valute(currencies, context.args[i])
            date = corr_date(response)
            message = (
                f'На {date}: \n'
                f'{currency}'
            )
            send_message(chat, context, message)
        except (InvalidValuteExc, InvalidApiExc, Exception) as error:
            message = f'Ошибка: {error}'
            logger.error(f'Сбой в работе программы: {error}')
            send_message(chat, context, message)
        else:
            logger.debug('Успешный запрос - нет исключений')


def main():
    updater = Updater(token=secret_token)
    updater.dispatcher.add_handler(CommandHandler('valutes', all_valutes))
    updater.dispatcher.add_handler(CommandHandler('currency', currency_rate))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, first_answer))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
