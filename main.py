import json
from turtledemo.paint import switchupdown

import hrequests
from bs4 import BeautifulSoup


def get_links():
    page = 1
    links = []

    while True:
        res = hrequests.get(f'https://www.nepremicnine.net/oglasi-prodaja/ljubljana-mesto/stanovanje/{page}/')

        soup = BeautifulSoup(res.text, 'lxml')

        elements = soup.find_all('a', class_='url-title-d')
        if len(elements) == 0:
            break

        print(f'Fetched page {page}')
        links += [element.get('href') for element in elements]

        page += 1

    return links


def get_page(url: str):
    res = hrequests.get(url)
    soup = BeautifulSoup(res.text, 'lxml')

    more_info = soup.find('div', class_='more_info').text.strip()
    infos = [info.split(': ')[1].strip() for info in more_info.split(' | ')]

    attr_items = [attr for attr in soup.find('ul', id='atributi').find_all('li') if
                  attr.get('class') is None]

    attributes = {}
    for attr in attr_items:
        text = attr.find(string=True, recursive=False)
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
        'price': float(soup.find('div', class_='cena').find('span').text.strip()
                       .replace(' €', '').replace('.', '').replace(',', '.')),
        'seller': soup.find('div', class_='prodajalec').text.strip(),
        'forwarding': infos[0],
        'type': infos[1],
        'region': infos[2],
        'administrative_unit': infos[3],
        'municipality': infos[4],
        'attributes': attributes,
        'short_description': soup.find('div', itemprop='description').text.strip(),
        'description': soup.find('div', itemprop='disambiguatingDescription').text.strip(),
    }

    print(json.dumps(item, indent=4, ensure_ascii=False))


get_page('https://www.nepremicnine.net/oglasi-prodaja/zg-siska-zgornja-stanovanje_6950088/')
