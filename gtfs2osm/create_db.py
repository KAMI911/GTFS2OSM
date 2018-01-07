import requests
import sqlalchemy
import sqlalchemy.orm
from sqlalchemy.sql import select
import pandas as pd
import re
import json
from bs4 import BeautifulSoup
from libs import address
from data_structure import Base, City, POI_address, POI_common

PATTERN_SPAR_REF = re.compile('\((.*?)\)')

def download_soup(link):
    page = requests.get(link, verify=False)
    return BeautifulSoup(page.content, 'html.parser') if page.status_code == 200 else None


def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance


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

    def add_city(self):
        xl = pd.ExcelFile('data/Iranyitoszam-Internet.XLS')
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

    def add_tesco(self):
        link_base = 'http://tesco.hu/aruhazak/nyitvatartas/'
        soup = download_soup('{}'.format(link_base))
        data = []
        try:
            get_or_create(self.session, POI_common, poi_name='Tesco Expressz', poi_tags='convenience', poi_url_base='https://www.tesco.hu')
            get_or_create(self.session, POI_common, poi_name='Tesco Extra', poi_tags='supermarket', poi_url_base='https://www.tesco.hu')
            get_or_create(self.session, POI_common, poi_name='Tesco', poi_tags='supermarket', poi_url_base='https://www.tesco.hu')
            self.session.commit()
        except Exception as e:
            print(e)
        finally:
            self.session.close()

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
                city = address.clean_city(poi_data[2].split(',')[0])
                postcode = poi_data[1].strip()
                try:
                    city_col = self.session.query(City.city_id).filter(City.city_name == city).filter(
                        City.city_post_code == postcode).first()
                    common_col = self.session.query(POI_common.pc_id).filter(POI_common.poi_name == name).first()
                    get_or_create(self.session, POI_address, poi_name=name, poi_branch=poi_data[0], poi_addr_city = city_col.city_id,
                                  poi_postcode=postcode, poi_city=city, poi_addr_street=street,
                                  poi_addr_housenumber=housenumber, poi_website=poi_data[4], poi_conscriptionnumber=conscriptionnumber, original=poi_data[3], poi_common_id=common_col)
                    self.session.commit()
                except Exception as e:
                    print(e)
                finally:
                    self.session.close()

    def add_aldi(self):
        link_base = 'https://www.aldi.hu/hu/informaciok/informaciok/uezletkereso-es-nyitvatartas/'
        soup = download_soup('{}'.format(link_base))
        data = []
        try:
            get_or_create(self.session, POI_common, poi_name='Aldi', poi_tags='supermarket', poi_url_base='https://www.aldi.hu')
            self.session.commit()
        except Exception as e:
            print(e)
        finally:
            self.session.close()
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
                city = address.clean_city(poi_data[1])
                postcode = poi_data[0].strip()
                name = 'Aldi'
                try:
                    city_col = self.session.query(City.city_id).filter(City.city_name == city).filter(
                        City.city_post_code == postcode).first()
                    common_col = self.session.query(POI_common.pc_id).filter(POI_common.poi_name == name).first()
                    get_or_create(self.session, POI_address, poi_name=name, poi_postcode=postcode, poi_addr_city = city_col, poi_city=city,
                                  poi_addr_street=street, poi_addr_housenumber=housenumber, poi_website=None, poi_conscriptionnumber=conscriptionnumber, original= poi_data[2], poi_common_id=common_col)
                    self.session.commit()
                except Exception as e:
                    print(e)
                finally:
                    self.session.close()

    def add_cba(self):
        link_base = 'http://www.cba.hu/uzletlista/'
        soup = download_soup('{}'.format(link_base))
        data = []
        try:
            get_or_create(self.session, POI_common, poi_name='CBA', poi_tags='convenience', poi_url_base='https://www.cba.hu')
            self.session.commit()
        except Exception as e:
            print(e)
        finally:
            self.session.close
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
                try:
                    city_col = self.session.query(City.city_id).filter(City.city_name == city).filter(
                        City.city_post_code == postcode).first()
                    common_col = self.session.query(POI_common.pc_id).filter(POI_common.poi_name == name).first()
                    get_or_create(self.session, POI_address, poi_name=name, poi_branch=poi_data['P_NAME'], poi_addr_city = city_col,
                                  poi_postcode=postcode, poi_city=city,
                                  poi_addr_street=street, poi_addr_housenumber=housenumber, poi_website=None, poi_conscriptionnumber=conscriptionnumber, original = poi_data['A_CIM'], poi_common_id=common_col)
                    self.session.commit()
                except Exception as e:
                    print(e)
                finally:
                    self.session.close()

    def add_rossmann(self):
        link_base = 'https://www.rossmann.hu/uzletkereso'
        soup = download_soup('{}'.format(link_base))
        data = []
        try:
            get_or_create(self.session, POI_common, poi_name='Rossmann', poi_tags='chemist', poi_url_base='https://www.rossmann.hu')
            self.session.commit()
        except Exception as e:
            print(e)
        finally:
            self.session.close
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
                city = address.clean_city(poi_data['city'])
                postcode = poi_data['addresses'][0]['zip'].strip()
                name = 'Rossmann'
                try:
                    city_col = self.session.query(City.city_id).filter(City.city_name == city).filter(
                        City.city_post_code == postcode).first()
                    common_col = self.session.query(POI_common.pc_id).filter(POI_common.poi_name == name).first()
                    get_or_create(self.session, POI_address, poi_name=name, poi_branch=None, poi_addr_city = city_col,
                                  poi_postcode=postcode, poi_city=city,
                                  poi_addr_street=street, poi_addr_housenumber=housenumber, poi_website=None, poi_conscriptionnumber=conscriptionnumber, original = poi_data['addresses'][0]['address'], poi_common_id=common_col)
                    self.session.commit()
                except Exception as e:
                    print(e)
                finally:
                    self.session.close()

    def add_spar(self):
        link_base = 'https://www.spar.hu/bin/aspiag/storefinder/stores?country=HU'
        soup = download_soup('{}'.format(link_base))
        data = []
        try:
            get_or_create(self.session, POI_common, poi_name='Spar Expressz', poi_tags='convenience',
                          poi_url_base='https://www.spar.hu')
            get_or_create(self.session, POI_common, poi_name='Interspar', poi_tags='supermarket',
                          poi_url_base='https://www.spar.hu')
            get_or_create(self.session, POI_common, poi_name='Spar', poi_tags='supermarket',
                          poi_url_base='https://www.spar.hu')
            self.session.commit()
        except Exception as e:
            print(e)
        finally:
            self.session.close
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
                city = address.clean_city(poi_data['city'])
                postcode = poi_data['zipCode']
                branch = poi_data['name'].split('(')[0].strip()
                ref_match = PATTERN_SPAR_REF.search(poi_data['name'])
                ref = ref_match.group(1).strip() if ref_match is not None else None
                try:
                    city_col = self.session.query(City.city_id).filter(City.city_name == city).filter(
                        City.city_post_code == postcode).first()
                    common_col = self.session.query(POI_common.pc_id).filter(POI_common.poi_name == name).first()
                    get_or_create(self.session, POI_address, poi_name=name, poi_branch=branch, poi_ref=ref, poi_addr_city = city_col,
                                  poi_postcode=postcode, poi_city=city,
                                  poi_addr_street=street, poi_addr_housenumber=housenumber,
                                  poi_website=poi_data['pageUrl'], poi_conscriptionnumber=conscriptionnumber, original = poi_data['address'], poi_common_id=common_col)
                    self.session.commit()
                except Exception as e:
                    print(e)
                finally:
                    self.session.close()


def main():
    db = POI_Base('postgresql://poi:poitest@localhost:5432')
    db.add_city()
    db.add_tesco()
    db.add_aldi()
    db.add_cba()
    db.add_spar()
    db.add_rossmann()


if __name__ == '__main__':
    main()
