#!/usr/bin/python
# -*- coding: utf-8 -*-

try:
    import logging, logging.config, os
    import numpy as np
    import pandas as pd
    from libs import g2o_stops_commandline
    from gtfs2osm.libs.osm import get_area_id, query_overpass
    from gtfs2osm.libs.file_output import generate_shape_xml
except ImportError as err:
    print('Error {0} import module: {1}'.format(__name__, err))
    exit(128)

__program__ = 'gtfs2osm-shape'
__version__ = '0.1.0'

def init_log():
    logging.config.fileConfig('log.conf')


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
        try:
            os.mkdir(output_folder)
        except FileExistsError as e:
            pass
        df_gtfs_shape = pd.read_csv(gtfs_data, dtype={'shape_id': 'str'})
        with open(os.path.join(output_folder, 'gtfs_shape.osm'), 'wb') as oxf:
            oxf.write(generate_shape_xml(df_gtfs_shape))
    except KeyboardInterrupt as e:
        logging.fatal('Processing is interrupted by the user.', exc_info=True)
    except IOError as e:
        logging.error('File error: {0}'.format(e), exc_info=True)
    except Exception as e:
        logging.error(e, exc_info=True)
