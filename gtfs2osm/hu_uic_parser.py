#!/usr/bin/python
# -*- coding: utf-8 -*-

# import libraries
import requests
import pandas as pd
import logging, logging.config, os
from bs4 import BeautifulSoup

period = '17' # 20xx: 2017 = 17
link_base = 'http://www.vpe.hu/takt'

def save_csv_file(path, file, data, message):
    # Save file to CSV file
    logging.info('Saving {0} to file: {1}'.format(message, file))
    res = data.to_csv(os.path.join(path, file), header=False)
    logging.info('The {0} was sucessfully saved'.format(file))

def download_soup(link):
    page = requests.get(link)
    return BeautifulSoup(page.content, 'html.parser') if page.status_code == 200 else None


soup = download_soup('{}/szh_lista.php?id_id=100000{}'.format(link_base, period))

data = []
if soup != None:
    # parse the html using beautiful soap and store in variable `soup`
    table = soup.find('table', attrs={'style': 'text-align: left;'})
    table_body = table.find('tbody')
    rows = table_body.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        # print(cols)
        link = cols[1].find('a').get('href') if cols[1].find('a') != None else []
        print('download')
        sub_soup = download_soup('{}/{}'.format(link_base, link))
        if sub_soup != None:
            table = sub_soup.find('table', attrs={'style': 'text-align: left;'})
            table_body = table.find('tbody')
            sub_rows = table_body.find_all('tr')
            add_cols = []
            for sub_row in sub_rows:
                sub_cols = sub_row.find_all('td')
                sub_cols = [element.text.strip() for element in sub_cols]
                add_cols.append(sub_cols[1])
        print('parse')
        cols = [element.text.strip() for element in cols]
        cols.append(link)
        if 'add_cols' in locals():
            cols.append(add_cols)
        print('done')
        data.append(cols)
    print('Writing')
    df = pd.DataFrame(data=data[1:], columns = data[0])
    save_csv_file(os.path.join('/common','git','GTFS2OSM', 'gtfs2osm', 'output_mav'), 'lista.csv', df, 'UIC data')
else:
    print ('Problem with download.')
