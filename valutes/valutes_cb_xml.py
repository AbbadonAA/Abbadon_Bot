import json
import logging
import re
import sys
from datetime import datetime as dt
from http import HTTPStatus

import requests
import xmltodict

from valutes.dicts import VALUTE_LIST
from valutes.exceptions import (EmptyListException, InvalidApiExc,
                                InvalidJsonExc, InvalidResponseExc,
                                InvalidType, InvalidValuteExc, NotValuteExc)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

REG = r'\b[A-Za-z]{3}\b'
CB_URL = 'https://cbr.ru/scripts/XML_daily.asp'


def url_for_date(dt_time):
    """Формирование корректного URL к API ЦБ."""
    if not isinstance(dt_time, dt):
        raise InvalidType('Неверный формат даты')
    date = dt_time.date()
    corr_date = date.strftime('%d/%m/%Y')
    url_add = f'?date_req={corr_date}'
    return CB_URL + url_add


def make_json(data):
    """Формирование JSON."""
    data = data.get('ValCurs')
    data = json.dumps(data)
    data = json.loads(data)
    json_all = {}
    json_all['@Date'] = data.get('@Date')
    json_valutes = {}
    for valute in data.get('Valute'):
        json_valutes[valute.get('CharCode')] = valute
    json_all['Valute'] = json_valutes
    return json_all


def get_api_answer(date=dt.today()):
    """Проверка успешности запроса к API."""
    try:
        response = requests.get(url_for_date(date))
    except Exception as error:
        raise InvalidApiExc(f'Ошибка ответа API: {error}')
    status = response.status_code
    if status != HTTPStatus.OK:
        logger.error(f'Ответ API: {status}')
        raise InvalidResponseExc(f'status_code: {status}')
    try:
        data = xmltodict.parse(response.content)
        return make_json(data)
    except Exception as error:
        raise InvalidJsonExc(f'Ошибка декодирования XML: {error}')


def check_data(data, context):
    """Проверка корректности данных."""
    if 'Valute' and '@Date' not in data:
        raise InvalidApiExc('Некорректный ответ API - нет Valute or Date')
    if not context:
        raise EmptyListException('Не указана валюта')
    charcode = context
    if re.match(REG, charcode) is None:
        raise NotValuteExc('Не соответствует Charcode')
    if charcode not in VALUTE_LIST:
        raise InvalidValuteExc(
            f'Валюта {charcode} некорректна или не поддерживается')
    try:
        return data.get('Valute')
    except Exception as error:
        raise InvalidApiExc(f'Не получены данные Valute: {error}')


def corr_date(response):
    """Перевод даты в нужный формат."""
    if '@Date' not in response:
        raise InvalidApiExc('Некорректный ответ API - Отсутствует Date')
    date = response.get('@Date')
    date = dt.strptime(date, '%d.%m.%Y')
    return date.strftime('%d.%m')


def parse_valute(data, context):
    """Получение курса валюты и подготовка сообщения."""
    currencies = check_data(data, context)
    currency = currencies.get(context)
    nominal = currency.get('Nominal').replace(',', '.')
    value = currency.get('Value').replace(',', '.')
    value = float(value) / float(nominal)
    return round(value, 3)
