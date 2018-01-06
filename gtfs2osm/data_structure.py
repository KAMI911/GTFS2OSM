from sqlalchemy import Column, ForeignKey, ForeignKeyConstraint, UniqueConstraint
from sqlalchemy import Integer, Unicode
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import synonym, relationship

Base = declarative_base()

class POI_address(Base):
    __tablename__ = 'poi_address'
    _plural_name_ = 'poi_address'
    pa_id = Column(Integer, primary_key=True, index=True)
    id = synonym('pa_id')
    #poi_osm_id = Column(Integer, nullable=False, unique=True, index=True)
    poi_osm_id = Column(Integer, unique=True, index=True)
    poi_name = Column(Unicode(64), nullable=False, index=True)
    poi_branch = Column(Unicode(64), nullable=True, index=True)
    poi_shop = Column(Unicode, nullable=False, index=True)
    poi_addr_city = Column(Integer, ForeignKey('city.city_id'), index=True)
    poi_postcode = Column(Integer)
    poi_city = Column(Unicode(64))
    poi_addr_street = Column(Unicode(64))
    poi_addr_housenumber = Column(Unicode(16))
    poi_conscriptionnumber = Column(Unicode(16))
    original = Column(Unicode(128))
    poi_website = Column(Unicode(128))
    poi_ref = Column(Unicode(16))

    def __repr__(self):
        return '<POI address {}: {}>'.format(self.poi_id, self.poi_name)

class City(Base):
    __tablename__ = 'city'
    _plural_name_ = 'city'
    city_id = Column(Integer, primary_key=True, index=True)
    id = synonym('city_id')
    city_name = Column(Unicode)
    city_post_code = Column(Integer)

    __table_args__ = (UniqueConstraint('city_name', 'city_post_code', name='uc_city_name_post_code'), )

    def __repr__(self):
        return '<City {}: {} ({})>'.format(self.city_id, self.city_name, self.city_post_code)
