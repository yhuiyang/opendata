#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging
import argparse
import subprocess


FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt=DATE_FORMAT)


def main():

    # command line parser
    parser = argparse.ArgumentParser(\
        description='''
The police stations data downloaded from 'http://data.gov.tw' contains x, y coordinates in TWD97 TM2 format (if you don't known what this means, see 'http://wiki.osgeo.org/wiki/Taiwan_datums' for basic concept). This script uses open source tool proj4 (http://proj.osgeo.org) to transform the x, y to WGS84 latlng format which can be located eaily on google map.''',
        epilog='Fell free to reuse, reproduction and/or redistribution.')
    parser.add_argument('-k', '--skip', metavar='N', default=0, type=int, help='Skip first N line. Use to  skip the data header. [default: 0]')
    parser.add_argument('-p', '--process', metavar='N', default=0, type=int, help='Process at most N line, 0 means all. [default: 0]')
    parser.add_argument('input_file', help='The raw data input file.')
    args = parser.parse_args()

    try:
        f = open(args.input_file, 'r')
    except IOError:
        logging.error('File does not exist.')
        return
    fout = open(args.input_file + '.out', 'w')

    line_count = 0
    processed_count = 0

    for line in f:

        line_count = line_count + 1
        if line_count <= args.skip:
            continue

        columns = line.rstrip().split(',')
        logging.debug(columns)

        p = subprocess.Popen(
            ['proj', '-I', '+proj=tmerc', '+lat_0=0', '+lon_0=121',
            '+x_0=250000', '+y_0=0', '+k=0.9999', '+ellps=WGS84',
            '-f', '%.6f', '-s'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        out = p.communicate(columns[3] + ' ' + columns[4])[0]
        p.stdout.close()

        latlng = out.split('\t')
        fout.write(line.rstrip() + ',' + latlng[0] + ',' + latlng[1])

        processed_count = processed_count + 1
        if args.process != 0 and processed_count >= args.process:
            break
        
    logging.info('Total line: %d, processed: %d' % (line_count, processed_count))

    fout.close()
    f.close()


if __name__ == '__main__':
    main()

