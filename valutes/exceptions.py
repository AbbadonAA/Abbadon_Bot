class InvalidApiExc(Exception):
    """Некорректный ответ API."""

    pass


class InvalidResponseExc(Exception):
    """Status_code != 200."""

    pass


class InvalidJsonExc(Exception):
    """Некорректное декодирование JSON."""

    pass


class EmptyListException(Exception):
    """Пустой список."""

    pass


class InvalidValuteExc(Exception):
    """Некорректно указан CharCode валюты."""

    pass


class NotValuteExc(Exception):
    """Некорректно указан CharCode валюты."""

    pass


class InvalidType(Exception):
    """Некорректный тип данных."""

    pass
