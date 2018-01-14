try:
    import requests
    import sqlalchemy
    import sqlalchemy.orm
    import pandas as pd
    import re
    import os
    import json
    import logging, logging.config
    from bs4 import BeautifulSoup
    from gtfs2osm.libs import address
    from gtfs2osm.dao.data_structure import Base, City, POI_address, POI_common
except ImportError as err:
    print('Error {0} import module: {1}'.format(__name__, err))
    exit(128)


__program__ = 'create_db'
__version__ = '0.2.0'


DOWNLOAD_CACHE = 'cache_url'
PATTERN_SPAR_REF = re.compile('\((.*?)\)')


def init_log():
    logging.config.fileConfig('log.conf')


def download_soup(link):
    page = requests.get(link, verify=False)
    return BeautifulSoup(page.content, 'html.parser') if page.status_code == 200 else None


def save_downloaded_soup(link, file):
    soup = download_soup(link)
    with open(file, mode="w", encoding="utf8") as code:
        code.write(str(soup.prettify()))
    return soup


def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance


def insert_type(session, type_data):
    try:
        for i in type_data:
            get_or_create(session, POI_common, poi_name=i['poi_name'], poi_tags=i['poi_tags'], poi_url_base=i['poi_url_base'])
    except Exception as e:
        print(e)


def insert(session, **kwargs):
    try:
        city_col = session.query(City.city_id).filter(City.city_name == kwargs['poi_city']).filter(
            City.city_post_code == kwargs['poi_postcode']).first()
        common_col = session.query(POI_common.pc_id).filter(POI_common.poi_name == kwargs['poi_name']).first()
        kwargs['poi_addr_city'] = city_col
        kwargs['poi_common_id'] = common_col
        get_or_create(session, POI_address, **kwargs )
        session.commit()
    except Exception as e:
        print(e)
    finally:
        session.close()

class POI_Base:
    """Represents the full database.

    :param db_conection: Either a sqlalchemy database url or a filename to be used with sqlite.

    """

    def __init__(self, db_connection):
        self.db_connection = db_connection
        self.db_filename = None
        if '://' not in db_connection:
            self.db_connection = 'sqlite:///%s' % self.db_connection
        if self.db_connection.startswith('sqlite'):
            self.db_filename = self.db_connection
        self.engine = sqlalchemy.create_engine(self.db_connection, echo=False)
        Session = sqlalchemy.orm.sessionmaker(bind=self.engine)
        self.session = Session()
        Base.metadata.create_all(self.engine)


    def add_poi_types(self, data):
        insert_type(self.session, data)


    def add_city(self, link_base):
        xl = pd.ExcelFile(link_base)
        df = xl.parse("Települések")
        for index, city_data in df.iterrows():
            try:
                get_or_create(self.session, City, city_post_code=city_data['IRSZ'], city_name=address.clean_city(city_data['Település']))
                self.session.commit()
            except Exception as e:
                print(e)
            finally:
                self.session.close()
        big_cities = [['Budapest', 'Bp.u.'],
                      ['Miskolc', 'Miskolc u.'],
                      ['Debrecen', 'Debrecen u.'],
                      ['Szeged', 'Szeged u.'],
                      ['Pécs', 'Pécs u.'],
                      ['Győr', 'Győr u.']
                      ]
        for city, sheet in big_cities:
            df = xl.parse(sheet)
            for index, city_data in df.iterrows():
                try:
                    get_or_create(self.session, City, city_post_code=city_data[0], city_name=city)
                    self.session.commit()
                except Exception as e:
                    print(e)
                finally:
                    self.session.close()


    def add_tesco(self, link_base):
        soup = save_downloaded_soup('{}'.format(link_base), os.path.join(DOWNLOAD_CACHE, 'tesco.html'))
        data = []
        if soup != None:
            # parse the html using beautiful soap and store in variable `soup`
            table = soup.find('table', attrs={'class': 'tescoce-table'})
            table_body = table.find('tbody')
            rows = table_body.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                link = cols[0].find('a').get('href') if cols[0].find('a') != None else []
                cols = [element.text.strip() for element in cols]
                cols[0] = cols[0].split('\n')[0]
                del cols[-1]
                del cols[-1]
                cols.append(link)
                data.append(cols)
            for poi_data in data:
                insert_row = {}
                # street, housenumobject does not support indexingber = address.extract_street_housenumber(poi_data[3])
                street, housenumber, conscriptionnumber = address.extract_street_housenumber_better(poi_data[3])
                tesco_replace = re.compile('(expressz{0,1})', re.IGNORECASE)
                poi_data[0] = tesco_replace.sub('Expressz', poi_data[0])
                if 'xpres' in poi_data[0]:
                    name = 'Tesco Expressz'
                elif 'xtra' in poi_data[0]:
                    name = 'Tesco Extra'
                else:
                    name = 'Tesco'
                poi_data[0] = poi_data[0].replace('TESCO', 'Tesco')
                poi_data[0] = poi_data[0].replace('Bp.', 'Budapest')

                insert(self.session, poi_city = address.clean_city(poi_data[2].split(',')[0]), poi_name = name, poi_postcode = poi_data[1].strip(), poi_branch = poi_data[0], poi_website = poi_data[4], original = poi_data[3], poi_addr_street = street, poi_addr_housenumber = housenumber, poi_conscriptionnumber = conscriptionnumber)


    def add_aldi(self, link_base):
        soup = save_downloaded_soup('{}'.format(link_base), os.path.join(DOWNLOAD_CACHE, 'aldi.html'))
        data = []
        if soup != None:
            # parse the html using beautiful soap and store in variable `soup`
            table = soup.find('table', attrs={'class': 'contenttable is-header-top'})
            table_body = table.find('tbody')
            rows = table_body.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                cols = [element.text.strip() for element in cols]
                data.append(cols)
            for poi_data in data:
                street, housenumber, conscriptionnumber = address.extract_street_housenumber_better(poi_data[2])
                name = 'Aldi'
                insert(self.session, poi_city = address.clean_city(poi_data[1]), poi_name = name, poi_postcode =  poi_data[0].strip(), poi_branch = None, poi_website = None, original = poi_data[2], poi_addr_street = street, poi_addr_housenumber = housenumber, poi_conscriptionnumber = conscriptionnumber)


    def add_cba(self, link_base):
        soup = save_downloaded_soup('{}'.format(link_base), os.path.join(DOWNLOAD_CACHE, 'cba.html'))
        data = []
        if soup != None:
            # parse the html using beautiful soap and store in variable `soup`
            pattern = re.compile('^\s*var\s*boltok_nyers.*')
            script = soup.find('script', text=pattern)
            m = pattern.match(script.get_text())
            data = m.group(0)
            data = address.clean_javascript_variable(data, 'boltok_nyers')
            text = json.loads(data)
            # for l in text:
            # print ('postcode: {postcode}; city: {city}; address: {address}; alt_name: {alt_name}'.format(postcode=l['A_IRSZ'], city=l['A_VAROS'], address=l['A_CIM'], alt_name=l['P_NAME']))

            for poi_data in text:
                street, housenumber, conscriptionnumber = address.extract_street_housenumber_better(poi_data['A_CIM'])
                city = address.clean_city(poi_data['A_VAROS'])
                postcode = poi_data['A_IRSZ'].strip()
                name = 'CBA'
                insert(self.session, poi_city = address.clean_city(poi_data['A_VAROS']), poi_name = name, poi_postcode =  poi_data['A_IRSZ'].strip(), poi_branch = poi_data['P_NAME'], poi_website = None, original = poi_data['A_CIM'], poi_addr_street = street, poi_addr_housenumber = housenumber, poi_conscriptionnumber = conscriptionnumber)


    def add_rossmann_types(self):
        data = [{'poi_name': 'Rossmann', 'poi_tags': "{'shop': 'chemist', 'operator': 'Rossmann Magyarország Kft.', 'brand':'Rossmann'}", 'poi_url_base': 'https://www.rossmann.hu'}]
        insert_type(self.session, data)


    def add_rossmann(self, link_base):
        soup = save_downloaded_soup('{}'.format(link_base), os.path.join(DOWNLOAD_CACHE, 'rossmann.html'))
        data = []
        if soup != None:
            # parse the html using beautiful soap and store in variable `soup`
            pattern = re.compile('^\s*var\s*places.*')
            script = soup.find('script', text=pattern)
            m = pattern.match(script.get_text())
            data = m.group(0)
            data = address.clean_javascript_variable(data, 'places')
            text = json.loads(data)
            # for l in text:
            # print ('postcode: {postcode}; city: {city}; address: {address}; alt_name: {alt_name}'.format(postcode=l['A_IRSZ'], city=l['A_VAROS'], address=l['A_CIM'], alt_name=l['P_NAME']))

            for poi_data in text:
                street, housenumber, conscriptionnumber = address.extract_street_housenumber_better(
                    poi_data['addresses'][0]['address'])
                name = 'Rossmann'

                insert(self.session, poi_city = address.clean_city(poi_data['city']), poi_name = name, poi_postcode = poi_data['addresses'][0]['zip'].strip(), poi_branch = None, poi_website = None, original = poi_data['addresses'][0]['address'], poi_addr_street = street, poi_addr_housenumber = housenumber, poi_conscriptionnumber = conscriptionnumber)


    def add_spar(self, link_base):
        soup = save_downloaded_soup('{}'.format(link_base), os.path.join(DOWNLOAD_CACHE, 'spar.json'))
        data = []
        if soup != None:
            text = json.loads(soup.get_text())
            for poi_data in text:
                street, housenumber, conscriptionnumber = address.extract_street_housenumber_better(poi_data['address'])
                if 'xpres' in poi_data['name']:
                    name = 'Spar Expressz'
                elif 'INTER' in poi_data['name']:
                    name = 'Interspar'
                elif 'market' in poi_data['name']:
                    name = 'Spar'
                else:
                    name = 'Spar'
                poi_data['name'] = poi_data['name'].replace('INTERSPAR', 'Interspar')
                poi_data['name'] = poi_data['name'].replace('SPAR', 'Spar')
                ref_match = PATTERN_SPAR_REF.search(poi_data['name'])
                ref = ref_match.group(1).strip() if ref_match is not None else None

                insert(self.session, poi_city = address.clean_city(poi_data['city']), poi_name = name, poi_postcode = poi_data['zipCode'].strip(), poi_branch = poi_data['name'].split('(')[0].strip(), poi_website = poi_data['pageUrl'].strip(), original = poi_data['address'], poi_addr_street = street, poi_addr_housenumber = housenumber, poi_conscriptionnumber = conscriptionnumber, poi_ref = ref)


    def add_kh_bank(self, link_base, name = 'K&H bank'):
        if link_base:
            with open(link_base, 'r') as f:
                text = json.load(f)
                for poi_data in text['results']:
                    first_element = next(iter(poi_data))
                    postcode, city, street, housenumber, conscriptionnumber = address.extract_all_address(poi_data[first_element]['address'])
                    insert(self.session, poi_city=city, poi_name=name,
                           poi_postcode=postcode, poi_branch=None,
                           poi_website=None, original=poi_data[first_element]['address'], poi_addr_street=street,
                           poi_addr_housenumber=housenumber, poi_conscriptionnumber=conscriptionnumber, poi_ref=None)


def main():
    init_log()
    logging.info('Starting {0} ...'.format(__program__))
    db = POI_Base('postgresql://poi:poitest@localhost:5432')
    logging.info('Importing cities ...'.format())
    db.add_city('data/Iranyitoszam-Internet.XLS')

    logging.info('Importing {} stores ...'.format('Tesco'))
    data = [{'poi_name': 'Tesco Expressz', 'poi_tags':"{'shop': 'convenience', 'operator': 'Tesco Global Áruházak Zrt.', 'brand': 'Tesco'}", 'poi_url_base': 'https://www.tesco.hu'},
            {'poi_name': 'Tesco Extra', 'poi_tags': "{'shop': 'supermarket', 'operator': 'Tesco Global Áruházak Zrt.', 'brand': 'Tesco'}", 'poi_url_base': 'https://www.tesco.hu'},
            {'poi_name': 'Tesco', 'poi_tags': "{'shop': 'supermarket', 'operator': 'Tesco Global Áruházak Zrt.', 'brand': 'Tesco'}", 'poi_url_base': 'https://www.tesco.hu'}]
    db.add_poi_types(data)
    db.add_tesco('http://tesco.hu/aruhazak/nyitvatartas/')

    logging.info('Importing {} stores ...'.format('Aldi'))
    data = [{'poi_name': 'Aldi', 'poi_tags': "{'shop': 'supermarket', 'operator': 'ALDI Magyarország Élelmiszer Bt.', 'brand': 'Aldi'}", 'poi_url_base': 'https://www.aldi.hu'}]
    db.add_poi_types(data)
    db.add_aldi('https://www.aldi.hu/hu/informaciok/informaciok/uezletkereso-es-nyitvatartas/')

    logging.info('Importing {} stores ...'.format('CBA'))
    data = [{'poi_name': 'CBA', 'poi_tags': "{'shop': 'convenience', 'brand': 'CBA'}", 'poi_url_base': 'https://www.cba.hu'}]
    db.add_poi_types(data)
    db.add_cba('http://www.cba.hu/uzletlista/')

    logging.info('Importing {} stores ...'.format('Spar'))
    data = [{'poi_name': 'Spar Expressz', 'poi_tags':"{'shop': 'convenience', 'operator': 'SPAR Magyarország Kereskedelmi Kft.', 'brand': 'Spar'}", 'poi_url_base': 'https://www.spar.hu'},
            {'poi_name': 'Interspar', 'poi_tags': "{'shop': 'supermarket', 'operator': 'SPAR Magyarország Kereskedelmi Kft.', 'brand': 'Spar'}", 'poi_url_base': 'https://www.spar.hu'},
            {'poi_name': 'Spar', 'poi_tags': "{'shop': 'supermarket', 'operator': 'SPAR Magyarország Kereskedelmi Kft.', 'brand': 'Spar'}", 'poi_url_base': 'https://www.spar.hu'}]
    db.add_poi_types(data)
    db.add_spar('https://www.spar.hu/bin/aspiag/storefinder/stores?country=HU')

    logging.info('Importing {} stores ...'.format('Rossmann'))
    db.add_poi_types(data)
    db.add_rossmann('https://www.rossmann.hu/uzletkereso')

    logging.info('Importing {} stores ...'.format('KH Bank'))
    data = [{'poi_name': 'K&H bank', 'poi_tags': "{'amenity': 'bank', 'brand': 'K&H', 'operator': 'K&H Bank Zrt.', bic': 'OKHBHUHB', 'atm': 'yes'}", 'poi_url_base': 'https://www.kh.hu'},
            {'poi_name': 'K&H', 'poi_tags': "{'amenity': 'atm', 'brand': 'K&H', 'operator': 'K&H Bank Zrt.'}", 'poi_url_base': 'https://www.kh.hu'}]
    db.add_poi_types(data)
    db.add_kh_bank(os.path.join(DOWNLOAD_CACHE, 'kh_bank.json'), 'K&H bank')
    db.add_kh_bank(os.path.join(DOWNLOAD_CACHE, 'kh_atm.json'), 'K&H')


if __name__ == '__main__':
    main()
