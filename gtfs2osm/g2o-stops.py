#!/usr/bin/python

try:
    import logging, logging.config, os
    import numpy as np
    import pandas as pd
    from OSMPythonTools.api import Api
    from scipy.spatial import distance
    from libs import g2o_stops_commandline
    from gtfs2osm.libs.osm import get_area_id, query_overpass
    from gtfs2osm.libs.file_output import save_csv_file, generate_stop_xml
    from gtfs2osm.libs.gis import finding_closest
except ImportError as err:
    print('Error {0} import module: {1}'.format(__name__, err))
    exit(128)

__program__ = 'gtfs2osm-stops'
__version__ = '0.3.0'

QUERY = {'bus': ['"highway"="bus_stop"'], 'tram': ['"railway"="tram_stop"'],
         'railway': ['"railway"="station"', '"railway"="halt"', '"railway"="platform"'],
         'other': ['"railway"="subway_entrance"', '"public_transport"="stop"', '"public_transport"="stop_position"',
                   '"public_transport"="stop_area"', '"public_transport"="platform"'],
         'bkk': ['"ref"="bkv"', '"ref:bkv"', '"bkk:ref"', '"ref:bkktelebusz"', '"public_transport:bkk"', '"ref:bkk"']}


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

        gtfs_data = os.path.join(input_folder, 'stops.txt')
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
                                                    e.tag('ref:bkv') if e.tag('ref:bkv') is not None else e.tag(
                                                        'ref:bkk') if e.tag('ref:bkk') is not None else e.tag(
                                                        'ref:bkktelebusz') if e.tag(
                                                        'ref:bkktelebusz') is not None else e.tag(
                                                        'code') if e.tag(
                                                        'code') is not None else e.tag(
                                                        'ref'), e.tag('ref:bkv'), e.tag('ref:bkk'),
                                                    e.tag('ref:bkktelebusz'),
                                                    e.tag('ref'), e.lat(), e.lon(), e.id(), e.tags(), None, None, None, None, None ] for e
                                                   in
                                                   osm_stops_query.elements()])
                        first_time = False
                    else:
                        logging.info('Aggregating addtitional OSM data from tag: {0} ...'.format(p))
                        if osm_stops_query.elements() != []:
                            osm_stops_list = np.concatenate((osm_stops_list, np.array([[e.tag('name'),
                                                                                        e.tag('ref:bkv') if e.tag(
                                                                                            'ref:bkv') is not None else e.tag(
                                                                                            'ref:bkk') if e.tag(
                                                                                            'ref:bkk') is not None else e.tag(
                                                                                            'ref:bkktelebusz') if e.tag(
                                                                                            'ref:bkktelebusz') is not None else e.tag(
                                                                                            'code') if e.tag(
                                                                                            'code') is not None else e.tag(
                                                                                            'ref'), e.tag('ref:bkv'),
                                                                                        e.tag('ref:bkk'),
                                                                                        e.tag('ref:bkktelebusz'),
                                                                                        e.tag('ref'), e.lat(), e.lon(),
                                                                                        e.id(),
                                                                                        e.tags(), None, None, None, None, None ] for
                                                                                       e in
                                                                                       osm_stops_query.elements()])),
                                                            axis=0)
        df_osm_stops = pd.DataFrame(osm_stops_list, columns=(
            'osm_name', 'osm_merged_refs', 'osm_ref_bkv', 'osm_ref_bkk', 'osm_ref_bkktelebusz', 'osm_ref',
            'osm_lat', 'osm_lon', 'osm_id', 'osm_tags', 'osm_version', 'osm_timestamp', 'osm_user', 'osm_uid', 'osm_changeset' ))
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

        save_csv_file(output_folder, 'all_osm_stops.csv', df_osm_stops, 'general list of all OSM elements')

        logging.info('Opening GTFS dataset ({0})'.format(gtfs_data))
        df_gtfs_stops = pd.read_csv(gtfs_data)

        save_csv_file(output_folder, 'all_gtfs_stops.csv', df_gtfs_stops, 'general list of all GTFS elements')

        logging.info('A GTFS dataset with {0} objects has loaded'.format(len(df_gtfs_stops)))

        frames = [df_gtfs_stops, df_osm_stops]
        logging.info('Concat OSM and GTF datasets')
        result = pd.concat(frames)
        save_csv_file(output_folder, 'concated_osm_gtfs_stops.csv', result, 'concat list of all GTFS elements')
        del result
        logging.info('Merging OSM and GTF datasets based on stop_id')
        result2 = pd.merge(df_gtfs_stops, df_osm_stops, left_on='stop_id', right_on='osm_merged_refs', how='outer')
        save_csv_file(output_folder, 'merged_osm_gtfs_stops.csv', result2, 'merged list of all GTFS elements')
        del result2
        logging.info('Merging OSM and GTF datasets based on name')
        result3 = pd.merge(df_gtfs_stops, df_osm_stops, left_on='stop_name', right_on='osm_name', how='inner')
        save_csv_file(output_folder, 'name_merged_osm_gtfs_stops.csv', result3, 'merged list of all GTFS elements based on name')
        with open(os.path.join(output_folder, 'osm_same_name.osm'), 'wb') as oxf:
            oxf.write(generate_stop_xml(result3, looking_for))
        del result3
        if 'bkk' in looking_for:
            df2 = df_gtfs_stops[~df_gtfs_stops['stop_id'].str.contains('CS')]
            result2 = pd.merge(df2, df_osm_stops, left_on='stop_id', right_on='osm_merged_refs', how='outer')
            save_csv_file(output_folder, 'merged_osm_gtfs_stops_without_cs.csv', result2,
                          'merged list of all GTFS elements (without BKK CS)')
            del result2, df2

        logging.info('Using new datasets')
        df1 = pd.DataFrame(df_gtfs_stops)
        df2 = pd.DataFrame(df_osm_stops)
        logging.info('Packing coordinates')
        df1['point'] = [(x, y) for x, y in zip(df1['stop_lat'], df1['stop_lon'])]
        df2['point'] = [(x, y) for x, y in zip(df2['osm_lat'], df2['osm_lon'])]
        df1_backup = df1
        df2_backup = df2
        save_csv_file(output_folder, 'closest_stops.csv', finding_closest(df1, df2),
                      'closest point list of all elements')
        with open(os.path.join(output_folder, 'osm_closest.osm'), 'wb') as oxf:
            oxf.write(generate_stop_xml(df2, looking_for))
        del df1, df2
        if 'bkk' in looking_for:
            df1 = df1_backup
            df2 = df2_backup
            df1 = df1[~df1['stop_id'].str.contains('CS')]
            save_csv_file(output_folder, 'closest_stops_without_cs.csv', finding_closest(df1, df2),
                          'closest point list of all elements (without BKK CS)')
            del df1, df2

    except KeyboardInterrupt as e:
        logging.fatal('Processing is interrupted by the user.', exc_info=True)
    except IOError as e:
        logging.error('File error: {0}'.format(e), exc_info=True)
    except Exception as e:
        logging.error(e, exc_info=True)
