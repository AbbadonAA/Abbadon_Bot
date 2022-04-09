import logging
import sys
from datetime import datetime as dt, timedelta

from send_message import send_message
from valutes.dicts import V_MOEX_R
from valutes.exceptions import InvalidApiExc, InvalidValuteExc, NotValuteExc
from valutes.valutes_cb import (check_data, corr_date, get_api_answer,
                                parse_valute, variation_cb)
from valutes.valutes_moex import get_moex_currency_rate


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def currency_rate(update, context):
    """Основная логика работы блока валюты."""
    chat = update.effective_chat
    for i in range(len(context.args)):
        try:
            logger.debug('Отправка запроса к API')
            response = get_api_answer()
            currencies = check_data(response, context.args[i])
            currency = parse_valute(currencies, context.args[i])
            date = corr_date(response)
            time = dt.now() + timedelta(hours=3)
            time = time.strftime('%H:%M')
            var = variation_cb(currencies, context.args[i])
            if context.args[i] not in V_MOEX_R:
                message = (
                    f'Курс {context.args[i]}:\n'
                    f'ЦБ РФ (на {date}): {currency} RUB ({var})'
                )
                send_message(chat, context, message)
            else:
                moex_now = get_moex_currency_rate(context.args[i], 'LAST')
                moex_open = get_moex_currency_rate(context.args[i], 'OPEN')
                var_mo = float(moex_now) - float(moex_open)
                var_round = f'{var_mo:.2f}'
                message = (
                    f'Курс {context.args[i]}:\n'
                    f'ЦБ РФ (на {date}): {currency} RUB ({var})\n'
                    f'MOEX  (на {time}): {moex_now} RUB ({var_round})'
                )
                send_message(chat, context, message)
        except NotValuteExc as error:
            logger.debug(f'Строка не является CharCode валюты: {error}')
        except InvalidValuteExc as error:
            message = f'{error}'
            logger.debug(f'{error}')
            send_message(chat, context, message)
        except (InvalidApiExc, Exception) as error:
            message = f'Ошибка: {error}'
            logger.error(f'Сбой в работе программы: {error}')
            send_message(chat, context, message)
        else:
            logger.debug('Успешный запрос - нет исключений')


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
