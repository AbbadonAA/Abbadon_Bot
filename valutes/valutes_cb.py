import logging
import re
import sys
from datetime import datetime as dt
from http import HTTPStatus

import requests

from valutes.dicts import VALUTE_LIST
from valutes.exceptions import (EmptyListException, InvalidApiExc,
                                InvalidJsonExc, InvalidResponseExc,
                                InvalidValuteExc, NotValuteExc)


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

CURRENCY_URL = 'https://www.cbr-xml-daily.ru/daily_json.js'
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
    date = correct_date.strftime('%d.%m')
    return date


def parse_valute(currencies, context):
    """Получение курса валюты и подготовка сообщения."""
    currency = currencies.get(context)
    value = currency.get('Value')
    value_round = round(value, 2)
    text = f'{value_round:.2f}'
    return text


def variation_cb(currencies, context):
    """Вывод отклонения курса ЦБ от вчерашнего."""
    currency = currencies.get(context)
    value = currency.get('Value')
    pr_value = currency.get('Previous')
    var = round(value - pr_value, 3)
    return var
