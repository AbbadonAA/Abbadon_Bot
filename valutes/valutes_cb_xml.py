import json
import logging
import re
import sys
from datetime import datetime as dt
from datetime import timedelta
from http import HTTPStatus

import requests
import xmltodict

from valutes.dicts import VALUTE_LIST
from valutes.exceptions import (EmptyListException, InvalidApiExc, InvalidDate,
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

TODAY = dt.now() + timedelta(hours=3)
REG = r'\b[A-Za-z]{3}\b'
CB_URL = 'https://cbr.ru/scripts/XML_daily.asp'
REG_DATE = r'\b(0[1-9]|[12][0-9]|3[0-1])[.](0[1-9]|1[0-2])[.](19|20)\d\d\b'


def date_args(date):
    """Перевод даты из context.args в корректный формат."""
    if re.match(REG_DATE, date) is None:
        raise InvalidDate(
            'Дата должна быть в формате dd.mm.yyyy')
    return dt.strptime(date, '%d.%m.%Y') + timedelta(hours=3)


def url_for_date(dt_time):
    """Формирование корректного URL к API ЦБ."""
    if not isinstance(dt_time, dt):
        raise InvalidType('Неверный формат даты')
    corr_date = dt_time.strftime('%d/%m/%Y')
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


def get_api_answer(date=TODAY):
    """Проверка успешности запроса к API."""
    min_date = dt.strptime('01.07.1992', '%d.%m.%Y')
    if date < min_date:
        raise InvalidDate('Начало отсчета 01.07.1992')
    if date > TODAY:
        date = TODAY
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
