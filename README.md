# GTFS2OSM

Tools to process GTFS data and import them to OSM.

## Installation

Clone or download this repository, then run pip:

    pip install -r requirements.txt

## g2o-stops utility

The g2o-stops utility reads GTFS stops.txt files and try to combine with OSM data.

Output files are joined GTFS and OSM datasets, based on stop_id or closest coordinates.

### Usage

g20-stops [-h] -i INPUT -o OUTPUT [-c CITY] [-t TYPE] [-v VEHICLE]

optional arguments:

-h, --help

    show this help message and exit

-i INPUT, --input INPUT

    required:  input folder

-o OUTPUT, --output OUTPUT

    required:  output folder

-c CITY, --city CITY

    optional:  city (default: Budapest)

-t TYPE, --type TYPE

    optional:  OSM object type

-v VEHICLE, --vehicle VEHICLE

optional:  OSM vechile  type

examples:
  g2o-stops.py -i ~/GTFS/bkk/ -o ./output_bkk/ -t node -v bus,tram,bkk

  g2o-stops.py -i ~/GTFS/mav/ -o ./output_mav/ -t node -v railway
