import logging
import sys
from datetime import datetime as dt
from http import HTTPStatus
import re

import requests
from send_message import send_message
from exceptions import (EmptyListException, InvalidApiExc, InvalidJsonExc,
                        InvalidResponseExc, InvalidValuteExc, NotValuteExc)

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
REG = r'\b[A-Za-z]{3}\b'


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
    """Получение списка поддерживаемых валют."""
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
    if re.match(REG, charcode) is None:
        raise NotValuteExc('Не соответствует CharCode')
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


def currency_rate_cb(update, context):
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
        except NotValuteExc as error:
            logger.debug(f'Строка не является CharCode валюты: {error}')
        except (InvalidValuteExc, InvalidApiExc, Exception) as error:
            message = f'Ошибка: {error}'
            logger.error(f'Сбой в работе программы: {error}')
            send_message(chat, context, message)
        else:
            logger.debug('Успешный запрос - нет исключений')
