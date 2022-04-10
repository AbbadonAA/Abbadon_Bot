import json
import logging
import re
import sys
from http import HTTPStatus

import requests

from valutes.dicts import V_MOEX, V_MOEX_R
from valutes.exceptions import InvalidJsonExc, InvalidResponseExc

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


MOEX_URL = ("https://iss.moex.com/iss/engines/currency/markets/selt/"
            "securities.jsonp?"
            "iss.only=marketdata&"
            f"securities={V_MOEX_R['USD']},{V_MOEX_R['EUR']},"
            f"{V_MOEX_R['GBP']},{V_MOEX_R['CHF']},{V_MOEX_R['CNY']},"
            f"{V_MOEX_R['JPY']},{V_MOEX_R['KZT']},{V_MOEX_R['TRY']},"
            f"{V_MOEX_R['HKD']},{V_MOEX_R['BYN']}&"
            "lang=ru&iss.meta=off&iss.json=extended&"
            "callback=angular.callbacks._gk")


def get_moex_answer():
    """Получение и обработка данных от MOEX."""
    try:
        response = requests.get(MOEX_URL)
    except Exception as error:
        raise InvalidResponseExc(f'Ошибка ответа MOEX: {error}')
    status = response.status_code
    if status != HTTPStatus.OK:
        logger.error(f'Ответ MOEX: {status}')
        raise InvalidResponseExc(f'status_code: {status}')
    try:
        data = response.text[22:len(response.text)-1]
        data = re.sub(r'\n', "", data)
        data = json.loads(data)
        data = data[1].get('marketdata')
    except Exception as error:
        raise InvalidJsonExc(f'Ошибка формирования JSON: {error}')
    return data


def moex_currency_dict(moment):
    """Формирование словаря валют и курсов."""
    currencies = {}
    for data in get_moex_answer():
        if data.get(moment):
            currencies[V_MOEX[data.get('SECID')][0]] = str(data.get(moment))
    return currencies


def get_moex_currency_rate(valute, moment):
    """Возврат курса для конкретной валюты."""
    currency = moex_currency_dict(moment)[valute]
    currency_round = round(float(currency), 2)
    return f'{currency_round:.2f}'