import logging
import sys
from datetime import datetime as dt
from datetime import timedelta

from send_message import send_message
from valutes.dicts import V_MOEX_R
from valutes.exceptions import (InvalidApiExc, InvalidDate, InvalidValuteExc,
                                NotValuteExc)
from valutes.valutes_cb_xml import (corr_date, date_args, get_api_answer,
                                    parse_valute)
from valutes.valutes_moex import get_moex_currency_rate

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

TODAY = dt.now() + timedelta(hours=3)
YESTERDAY = TODAY - timedelta(days=1)


def currency_rate(update, context):
    """Основная логика работы блока валюты."""
    chat = update.effective_chat
    for i in range(len(context.args)):
        try:
            logger.debug('Отправка запроса к API')
            charcode = context.args[i].upper()
            response_last = get_api_answer(TODAY)
            response_prev = get_api_answer(YESTERDAY)
            currency_tod = parse_valute(response_last, charcode)
            currency_prev = parse_valute(response_prev, charcode)
            var = currency_tod - currency_prev
            date = corr_date(response_last)
            time = TODAY
            time = time.strftime('%H:%M')
            if charcode not in V_MOEX_R:
                message = (
                    f'Курс {charcode}:\n'
                    f'ЦБ РФ (на {date}): {currency_tod:.3f} RUB ({var:.3f})'
                )
                send_message(chat, context, message)
            else:
                moex_now = get_moex_currency_rate(charcode, 'LAST')
                moex_open = get_moex_currency_rate(charcode, 'OPEN')
                var_mo = float(moex_now) - float(moex_open)
                var_round = f'{var_mo:.2f}'
                message = (
                    f'Курс {charcode}:\n'
                    f'ЦБ РФ (на {date}): {currency_tod:.3f} RUB ({var:.3f})\n'
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
    """Получение списка валют и курсов ЦБ на дату."""
    chat = update.effective_chat
    try:
        if not context.args:
            date = TODAY
        else:
            date = date_args(context.args[0])
        response = get_api_answer(date)
        valutes = response.get('Valute').keys()
        valutes_name = response.get('Valute')
    except InvalidDate as error:
        logger.info(f'Ошибка в дате: {error}')
        message = f'{error}'
        send_message(chat, context, message)
    except Exception as error:
        logger.error(f'Получение ключей Valute: {error}')
        raise InvalidApiExc(f'Некорректный ответ API - {error}')
    else:
        message_list = []
        for valute in valutes:
            try:
                name = valutes_name.get(valute).get('Name')
                value = valutes_name.get(valute).get('Value')
                nominal = valutes_name.get(valute).get('Nominal')
                value = value.replace(',', '.')
                value = float(value) / float(nominal)
            except Exception as error:
                logger.error(f'Ошибка в Name or Value: {error}')
                raise InvalidApiExc(f'Проблемы с Name or Value: {error}')
            else:
                message_list.append(f'{valute} - {name} - {value:.2f}')
        message = '\n'.join(message_list)
        date = response.get('@Date')
        message = f'Курсы валют на {date}:\n{message}'
        send_message(chat, context, message)
