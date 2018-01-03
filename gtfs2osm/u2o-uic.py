#!/usr/bin/python

try:
    import logging, logging.config, os
    import numpy as np
    import pandas as pd
    from OSMPythonTools.api import Api
    from scipy.spatial import distance
    from libs import g2o_stops_commandline
    from gtfs2osm.libs.osm import get_area_id, query_overpass
    from gtfs2osm.libs.file_output import save_csv_file, generate_uic_xml
    from gtfs2osm.libs.gis import match_value

except ImportError as err:
    print('Error {0} import module: {1}'.format(__name__, err))
    exit(128)

__program__ = 'uic2osm-stops'
__version__ = '0.1.0'

QUERY = {'railway': ['"railway"="station"', '"railway"="halt"' ]}


def init_log():
    logging.config.fileConfig('log.conf')


if __name__ == '__main__':
    try:
        init_log()
        logging.info('Starting {0} ...'.format(__program__))
        # Reading command line parameters
        cmd = g2o_stops_commandline.g2o_stops_commandline()
        cmd.parse()
        city = cmd.city
        input_folder = cmd.input
        output_folder = cmd.output
        osm_type = cmd.type
        looking_for = cmd.vehicle

        uic_data = os.path.join(input_folder, 'ALLOMASOK_UIC.xlsx')
        # Query Nominatim
        local_area_id = get_area_id(city)
        logging.info('Query Nominatim for area: {0}'.format(city))

        first_time = True
        # Query overpass
        for t in osm_type:
            for v in looking_for:
                for p in QUERY[v]:
                    logging.info('Query OSM for object: {0}, looking for: {1}, with tag: {2} ...'.format(t, v, p))
                    osm_stops_query = query_overpass(str(local_area_id), p, t)
                    if first_time:
                        osm_stops_list = np.array([[e.tag('name'),
                                                    e.tag('uic_ref'), e.tag('uic_name'),e.lat(), e.lon(), e.id(), e.tags(), None, None, None, None, None ] for e
                                                   in
                                                   osm_stops_query.elements()])
                        first_time = False
                    else:
                        logging.info('Aggregating addtitional OSM data from tag: {0} ...'.format(p))
                        if osm_stops_query.elements() != []:
                            osm_stops_list = np.concatenate((osm_stops_list, np.array([[e.tag('name'),
                                                                                        e.tag('uic_ref'),
                                                                                        e.tag('uic_name'), e.lat(),
                                                                                        e.lon(), e.id(), e.tags(), None,
                                                                                        None, None, None, None] for e in
                                                                                       osm_stops_query.elements()])),
                                                            axis=0)
        df_osm_stops = pd.DataFrame(osm_stops_list, columns=(
            'osm_name', 'uic_ref', 'uic_name', 'osm_lat', 'osm_lon', 'osm_id', 'osm_tags', 'osm_version', 'osm_timestamp', 'osm_user', 'osm_uid', 'osm_changeset' ))
        logging.info('Number of elements after all OSM queries: {0}'.format(len(df_osm_stops)))
        df_osm_stops.drop_duplicates(subset='osm_id', keep='first', inplace=True)
        logging.info('Number of elements after removing duplicates based on OSMID: {0}'.format(len(df_osm_stops)))
        api = Api()
        for index, osm_data in df_osm_stops.iterrows():
            node = api.query('node/{}'.format(osm_data['osm_id']))
            try:
                df_osm_stops.loc[[index], 'osm_timestamp'] = node.timestamp()
                if node.uid() != None and node.user != None:
                    df_osm_stops.loc[[index], 'osm_uid'] = node.uid()
                    df_osm_stops.loc[[index], 'osm_user'] = node.user()
                else:
                    df_osm_stops.loc[[index], 'osm_uid'] = '4579407'
                    df_osm_stops.loc[[index], 'osm_user'] = 'OSM_KAMI'
                df_osm_stops.loc[[index], 'osm_changeset'] = node.changeset()
                if node.version() != None:
                    df_osm_stops.loc[[index], 'osm_version'] = node.version()
                else:
                    df_osm_stops.loc[[index], 'osm_version'] = '55'
            except IOError as e:
                logging.error('File error: {0}'.format(e), exc_info=True)

        try:
            os.mkdir(output_folder)
        except FileExistsError as e:
            pass

        save_csv_file(output_folder, 'all_osm_stations.csv', df_osm_stops, 'general list of all OSM elements')

        logging.info('Opening UIC dataset ({0})'.format(uic_data))
        xl = pd.ExcelFile(uic_data)
        df_gtfs_stops = xl.parse("Állomások")

        save_csv_file(output_folder, 'all_uic_stations.csv', df_gtfs_stops, 'general list of all UIC elements')

        logging.info('A UIC dataset with {0} objects has loaded'.format(len(df_gtfs_stops)))

        frames = [df_gtfs_stops, df_osm_stops]

        logging.info('Merging OSM and UIC datasets based on name')
        result3 = pd.merge(df_gtfs_stops, df_osm_stops, left_on='Név', right_on='osm_name', how='inner')
        save_csv_file(output_folder, 'name_merged_osm_uic.csv', result3, 'merged list of all UIC elements based on name')
        with open(os.path.join(output_folder, 'osm_uic.osm'), 'wb') as oxf:
            oxf.write(generate_uic_xml(result3, looking_for))
        del result3

    except KeyboardInterrupt as e:
        logging.fatal('Processing is interrupted by the user.', exc_info=True)
    except IOError as e:
        logging.error('File error: {0}'.format(e), exc_info=True)
    except Exception as e:
        logging.error(e, exc_info=True)
