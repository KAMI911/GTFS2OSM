#!/usr/bin/python

try:
    import logging, logging.config, os
    import numpy as np
    import pandas as pd
    from libs import g2o_stops_commandline


except ImportError as err:
    print('Error {0} import module: {1}'.format(__name__, err))
    exit(128)

__program__ = 'gtfs2osm-shape'
__version__ = '0.0.0'

def init_log():
    logging.config.fileConfig('log.conf')


def save_csv_file(path, file, data, message):
    # Save file to CSV file
    logging.info('Saving {0} to file: {1}'.format(message, file))
    res = data.to_csv(os.path.join(path, file))
    logging.info('The {0} was sucessfully saved'.format(file))

def ascii_numcoder(text):
    output = ''
    for i in text:
        if i in range(0,10,1):
            output += i
        else:
            output += str(ord(i))
    return output

def generate_xml(pd):
    from lxml import etree
    import lxml
    osm_xml_data = etree.Element('osm', version='0.6', generator='JOSM')
    old_shape_id = 0
    for index, row in pd.iterrows():
        data = etree.SubElement(osm_xml_data, 'node', action='modify', id='-{}{}'.format(ascii_numcoder(row['shape_id']), row['shape_pt_sequence']), lat='{}'.format(row['shape_pt_lat']), lon='{}'.format(row['shape_pt_lon']))
    for index, row in pd.iterrows():
        if old_shape_id != ascii_numcoder(row['shape_id']):
            print ('{}   {} not same'.format(old_shape_id, ascii_numcoder(row['shape_id'])))
            way = etree.SubElement(osm_xml_data, 'way', id='-{}'.format(ascii_numcoder(row['shape_id'])))
            old_shape_id = ascii_numcoder(row['shape_id'])
        nd = etree.SubElement(way, 'nd', ref='-{}{}'.format(ascii_numcoder(row['shape_id']), row['shape_pt_sequence']))
    osm_xml_data.append(way)
    return lxml.etree.tostring(osm_xml_data, pretty_print=True, xml_declaration=True, encoding="UTF-8")


if __name__ == '__main__':
    try:
        init_log()
        logging.info('Starting {0} ...'.format(__program__))
        # Reading command line parameters
        cmd = g2o_stops_commandline.g2o_stops_commandline()
        cmd.parse()
        input_folder = cmd.input
        output_folder = cmd.output
        gtfs_data = os.path.join(input_folder, 'shapes.txt')
        '''
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
        '''
        try:
            os.mkdir(output_folder)
        except FileExistsError as e:
            pass
        df_gtfs_shape = pd.read_csv(gtfs_data, dtype={'shape_id': 'str'})
        with open(os.path.join(output_folder, 'gtfs_shape.osm'), 'wb') as oxf:
            oxf.write( generate_xml(df_gtfs_shape))
    except KeyboardInterrupt as e:
        logging.fatal('Processing is interrupted by the user.', exc_info=True)
    except IOError as e:
        logging.error('File error: {0}'.format(e), exc_info=True)
    except Exception as e:
        logging.error(e, exc_info=True)
