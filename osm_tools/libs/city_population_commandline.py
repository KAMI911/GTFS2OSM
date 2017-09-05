try:
    import argparse, textwrap, os, sys, atexit, logging, logging.config

except ImportError as err:
    print('Error {0} import module: {1}'.format(__name__, err))
    exit(128)


class city_population_commandline:
    def __init__(self):
        self.parser = argparse.ArgumentParser(prog="city_population",
                                              formatter_class=argparse.RawTextHelpFormatter,
                                              description='',
                                              epilog=textwrap.dedent('''
        examples:
          city_population.py --i ~/GTFS/bkk/ -o ./output_bkk/ -t node -v bus,tram,bkk

          city_population.py --i ~/GTFS/mav/ -o ./output_mav/ -t node -v railway

        '''))

        self.parser.add_argument('-i', '--input', type=str, dest='input', required=True,
                                 help='required:  input file')

        self.parser.add_argument('-o', '--output', type=str, dest='output', required=True,
                                 help='required:  output folder')

        self.parser.add_argument('-a', '--area', type=str, dest='area', required=False, default='Hungary',
                                 help='optional:  area (default: Hungary)')

    def parse(self):
        self.args = self.parser.parse_args()

    @property
    def input(self):
        return self.args.input

    @property
    def output(self):
        return self.args.output

    @property
    def area(self):
        return self.args.area
