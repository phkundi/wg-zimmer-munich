import sys
import requests
import time
import datetime
from bs4 import BeautifulSoup
from sheets import sheet

room_type = sys.argv[1]

def makeCollection(type_):
    if type_ == 'zimmer':
        url = 'https://www.wg-gesucht.de/wg-zimmer-in-Muenchen.90.0.0.0.html'  # wg zimmer
    elif type_ == 'wohnung':
        url = 'https://www.wg-gesucht.de/1-zimmer-wohnungen-in-Muenchen.90.1.0.0.html' # 1 zimmer wohnung

    base_url = 'https://www.wg-gesucht.de/'
    collection = []

    while True:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        rooms = soup.select('.offer_list_item')
        next_button = soup.select('.pagination')[0].find_all('li')[-1]

        print('Daten sammeln')
        for room in rooms:
            link = base_url + room['adid']
            room_id = room['data-id']
            online_since = room.find(class_='ang_spalte_datum').find(
                'a').find('span').get_text().strip()
            rent = room.find(class_='ang_spalte_miete').find(
                'a').find('span').get_text().strip()
            size = room.find(class_='ang_spalte_groesse').find(
                'a').find('span').get_text().strip()
            location = room.find(class_='ang_spalte_stadt').find(
                'a').find('span').get_text().replace('München', '').strip()

            from_date_raw = room.find(class_='ang_spalte_freiab').find(
                'a').find('span').get_text().strip()
            from_date = datetime.datetime.strptime(from_date_raw, '%d.%m.%Y')

            if room.find(class_='ang_spalte_freibis').find('a').find('span'):
                to_date_raw = room.find(class_='ang_spalte_freibis').find(
                    'a').find('span').get_text().strip()
                to_date = datetime.datetime.strptime(to_date_raw, '%d.%m.%Y')
            else:
                to_date = None

            collection.append(
                {
                    'id': room_id,
                    'posted': online_since,
                    'rent': rent,
                    'size': size,
                    'location': location,
                    'from': from_date,
                    'to': to_date,
                    'link': link
                }
            )

        # muss geändert werden bei wechsel zw zimmer und wohnung
        if type_ == 'zimmer':
            if '90.0.0.10' in next_button.find('a')['href']: # wg zimmer
                break
        elif type_ == 'wohnung':
            if '90.1.0.4' in next_button.find('a')['href']:
                break
        url = base_url + next_button.find('a')['href']
        time.sleep(2)

    return collection

def write(collection):
    ids = sheet.col_values(1)
    print('Daten filtern')
    for item in collection:
        if item['id'] not in ids:
            if item['to']:
                start_date = datetime.datetime.strptime(
                    '01.05.2019', '%d.%m.%Y')
                end_date = datetime.datetime.strptime('01.08.2019', '%d.%m.%Y')
                margin = datetime.timedelta(days=5)

                if item['to'] - margin <= end_date <= item['to'] + margin:
                    print('Daten eintragen')
                    new_entry = [item['id'], item['from'].date().strftime('%d.%m.%Y'), item['to'].date().strftime(
                        '%d.%m.%Y'), item["rent"], item["size"], item['location'], item['posted'], item['link']]
                    sheet.insert_row(new_entry, 2)


col = makeCollection(room_type)
write(col)
