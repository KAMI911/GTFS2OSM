from OSMPythonTools.nominatim import Nominatim
from OSMPythonTools.overpass import overpassQueryBuilder


def get_area_id(area):
    # Query Nominatom
    nominatim = Nominatim()
    return nominatim.query(area).areaId()


def query_overpass(area_id, query_statement, element_type='node'):
    # Query Overpass based on area
    global overpass
    query = overpassQueryBuilder(area=area_id, elementType=element_type, selector=query_statement)
    return overpass.query(query)