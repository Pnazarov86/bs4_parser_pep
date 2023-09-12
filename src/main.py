import logging
import re
from collections import defaultdict
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import (
    BASE_DIR, DOWNLOADS_DIR, EXPECTED_STATUS, MAIN_DOC_URL, PEP_DOC_URL
)
from exceptions import ParserFindTagException, ParserDefinitionException
from outputs import control_output
from utils import find_tag, get_response, get_soup


def whats_new(session):
    """Парсинг обновлений документации Python."""
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    soup = get_soup(session, whats_new_url)
    if soup is None:
        return
    main_div = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})
    div_with_ul = find_tag(main_div, 'div', attrs={'class': 'toctree-wrapper'})
    sections_by_python = div_with_ul.find_all(
        'li', attrs={'class': 'toctree-l1'}
    )

    result = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]
    for section in tqdm(sections_by_python):
        version_a_tag = section.find('a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        response = get_response(session, version_link)
        if response is None:
            continue
        soup = BeautifulSoup(response.text, 'lxml')
        h1 = find_tag(soup, 'h1')
        dl = find_tag(soup, 'dl')
        dl_text = dl.text.replace('\n', ' ')
        result.append((version_link, h1.text, dl_text))

    return result


def latest_versions(session):
    """Парсинг версий документации Python."""
    soup = get_soup(session, MAIN_DOC_URL)
    if soup is None:
        return
    sidebar = find_tag(soup, 'div', {'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise ParserFindTagException('Ничего не нашлось')

    result = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        link = a_tag['href']
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''

        result.append(
            (link, version, status)
        )

    return result


def download(session):
    """Загружает документацию Python."""
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    soup = get_soup(session, downloads_url)
    if soup is None:
        return
    main_tag = find_tag(soup, 'div', {'role': 'main'})
    table_tag = find_tag(main_tag, 'table', {'class': 'docutils'})
    pdf_a4_tag = find_tag(
        table_tag, 'a', {'href': re.compile(r'.+pdf-a4\.zip$')}
    )
    pdf_a4_link = pdf_a4_tag['href']
    archive_url = urljoin(downloads_url, pdf_a4_link)
    filename = archive_url.split('/')[-1]
    downloads_dir = BASE_DIR / DOWNLOADS_DIR
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename
    response = session.get(archive_url)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(f'Архив был загружен и сохранён: {archive_path}')


def pep(session):
    """Парсинг статусов PEP."""
    soup = get_soup(session, PEP_DOC_URL)
    if soup is None:
        return
    section_tag = find_tag(soup, 'section', attrs={'id': 'numerical-index'})
    tbody_tag = find_tag(section_tag, 'tbody')
    tr_tags = tbody_tag.find_all('tr')
    pep_count = defaultdict(int)

    result = [('Статус', 'Количество')]
    for tr_tag in tqdm(tr_tags):
        td_tag = find_tag(tr_tag, 'td')
        preview_status = td_tag.text[1:]
        a_tag = find_tag(tr_tag, 'a')
        href = a_tag['href']
        link = urljoin(PEP_DOC_URL, href)
        response = get_response(session, link)
        if response is None:
            continue
        soup = BeautifulSoup(response.text, 'lxml')
        dl_tag = find_tag(soup, 'dl')
        status = dl_tag.find(string=re.compile(r'^Status$')).parent
        status_card = status.next_sibling.next_sibling.text
        if status_card not in pep_count:
            pep_count[status_card] = 0
        pep_count[status_card] += 1
        if status_card not in EXPECTED_STATUS[preview_status]:
            logging.info(
                'Несовпадающие статусы:\n'
                f'{link}\n'
                f'Статус в карточке: {status_card}\n'
                f'Ожидаемые статусы: '
                f'{EXPECTED_STATUS[preview_status]}\n'
            )
    pep_count['Total'] = sum([value for value in pep_count.values()])
    result.extend(pep_count.items())

    return result


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep
}


def main():
    """Главная функция."""
    configure_logging()
    logging.info('Парсер запущен!')
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f'Аргументы командной строки: {args}')
    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()
    parser_mode = args.mode
    try:
        results = MODE_TO_FUNCTION[parser_mode](session)
    except Exception as error:
        error_msg = f'Ошибка в работе функции {error}'
        logging.error(error_msg)
        raise ParserDefinitionException(error_msg)
    if results is not None:
        control_output(results, args)
    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
