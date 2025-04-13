import re
import csv
import hrequests
from multiprocessing import Pool
from bs4 import BeautifulSoup, Tag


def get_urls():
    page = 1

    while True:
        print(f'page: {page}')
        res = hrequests.get(f'https://www.nepremicnine.net/oglasi-oddaja/{page}/')

        soup = BeautifulSoup(res.text, 'lxml')

        elements = soup.find_all('a', class_='url-title-d')
        if len(elements) == 0:
            break

        for element in elements:
            yield element.get('href')

        page += 1


def text_or_none(el: Tag):
    if el is None:
        return None
    return el.text.strip().replace('\n', ' ')


def parse_post(url: str):
    print(url)
    try:
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
                value = p[1] if len(p) == 2 else True

                match key:
                    case 'Velikost':
                        value = float(value.split()[0].replace('.', '').replace(',', '.'))
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
                re.findall("([0-9]+(?:[.,][0-9]+)*)",
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

    except Exception as e:
        print(e)
        return None


def main():
    fieldnames = {'id', 'url', 'name', 'price', 'seller', 'forwarding', 'type', 'region', 'administrative_unit',
                  'municipality', 'attributes', 'short_description', 'description'}

    with open('nepremicnine_oddaja.csv', mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        with Pool(processes=10) as pool:
            posts = pool.imap(parse_post, get_urls())

            for post in posts:
                if post is None:
                    continue
                writer.writerow(post)


if __name__ == '__main__':
    main()
