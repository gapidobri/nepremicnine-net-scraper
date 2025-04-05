import json
import re

import hrequests
from bs4 import BeautifulSoup, Tag

errors = open('errors.txt', 'w')


def text_or_none(el: Tag):
    if el is None:
        return None
    return el.text.strip()


def get_pages():
    page = 1
    items = []

    while True:
        res = hrequests.get(f'https://www.nepremicnine.net/oglasi-prodaja/ljubljana-mesto/stanovanje/{page}/')

        soup = BeautifulSoup(res.text, 'lxml')

        elements = soup.find_all('a', class_='url-title-d')
        if len(elements) == 0:
            break

        for element in elements:
            try:
                items.append(get_page(element.get('href')))
            except Exception as e:
                print(e)
                errors.write(element.get('href'))
                errors.write('\n')
                errors.write(f'{e}\n\n')

        page += 1
    return items


def get_page(url: str):
    print('Fetching page', url)
    res = hrequests.get(url)
    soup = BeautifulSoup(res.text, 'lxml')

    more_info = text_or_none(soup.find('div', class_='more_info'))
    infos = [info.split(': ')[1].strip() for info in more_info.split(' | ')]

    attributes = {}
    attr_el = soup.find('ul', id='atributi')
    if attr_el is not None:
        attr_items = [attr for attr in attr_el.find_all('li') if
                      attr.get('class') is None]

        for attr in attr_items:
            text = attr.find(string=True, recursive=False)
            if text is None:
                continue
            p = text.split(': ')
            key = p[0]
            if len(p) == 2:
                value = p[1]
            else:
                value = True

            match key:
                case 'Velikost':
                    value = float(value.split()[0].replace(',', '.'))
                case 'Št. spalnic' | 'Št. kopalnic' | 'Lastniško parkirno mesto':
                    value = int(value)

            if 'kWh' in attr.text:
                value = key
                key = 'Energijski razred'

            attributes[key] = value

    ids = soup.find_all('div', class_='dsc')

    item = {
        'id': int(ids[len(ids) - 1].text.strip()),
        'url': url,
        'name': soup.find('h1', itemprop='name').text,
        'price': float(
            re.findall("([0-9.,]+)",
                       soup.find('div', class_='cena').find('span').find(string=True, recursive=False).strip())[0]
            .replace('.', '')
            .replace(',', '.')
        ),
        'seller': soup.find('div', class_='prodajalec').text.strip(),
        'forwarding': infos[0],
        'type': infos[1],
        'region': infos[2],
        'administrative_unit': infos[3],
        'municipality': infos[4],
        'attributes': attributes,
        'short_description': text_or_none(soup.find('div', itemprop='description')),
        'description': text_or_none(soup.find('div', itemprop='disambiguatingDescription')),
    }

    return item


i = get_pages()

file = open('export.json', 'w')

file.write(json.dumps(i, indent=4, ensure_ascii=False))

file.close()
errors.close()
