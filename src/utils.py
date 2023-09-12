import logging
from bs4 import BeautifulSoup

from requests import RequestException

from exceptions import ParserFindTagException


def get_soup(session, url):
    """Создание супа."""
    response = get_response(session, url)
    if response is None:
        return
    return BeautifulSoup(response.text, features='lxml')


def get_response(session, url, encoding='utf-8'):
    """Перехват ошибки RequestException."""
    try:
        response = session.get(url)
        response.encoding = encoding
        return response
    except RequestException:
        logging.exception(
            f'Возникла ошибка при загрузке страницы {url}',
            stack_info=True
        )


def find_tag(soup, tag, attrs=None):
    """Перехват ошибки поиска тегов."""
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        error_msg = f'Не найден тег {tag} {attrs}'
        logging.error(error_msg, stack_info=True)
        raise ParserFindTagException(error_msg)
    return searched_tag
