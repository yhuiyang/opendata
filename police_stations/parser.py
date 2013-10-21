#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging
import argparse
import subprocess


FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def main():

    # command line parser
    parser = argparse.ArgumentParser(\
        description='''
The police stations data downloaded from 'http://data.gov.tw' contains x, y coordinates in TWD97 TM2 format (if you don't known what this means, see 'http://wiki.osgeo.org/wiki/Taiwan_datums' for basic concept). This script uses open source tool proj4 (http://proj.osgeo.org) to transform the x, y to WGS84 latlng format which can be located easily on google map.''',
        epilog='Feel free to reuse, reproduction and/or redistribution.')
    parser.add_argument('-p', '--process', metavar='N', default=0, type=int, help='Process at most N lines, 0 means all. [default: 0]')
    parser.add_argument('-v', '--verbose', action='count', help='Enable verbose debug message.')
    parser.add_argument('input_file', help='The raw data input file.')
    args = parser.parse_args()

    # config logging level
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format=FORMAT, datefmt=DATE_FORMAT)
    else:
        logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt=DATE_FORMAT)

    # prepare input/output files
    try:
        f = open(args.input_file, 'r')
    except IOError:
        logging.error('File does not exist.')
        return
    fout = open(args.input_file + '.out', 'w')

    # process start
    line_count = 0
    processed_count = 0

    # processed line by line
    for line in f:

        line_count = line_count + 1

        # The 1st line is always the header line, just record the column title and skip processing
        if line_count == 1:
            header_title = line.rstrip().split(',')
            column_empty_count = [0] * len(header_title)
            continue

        # real data column
        columns = line.rstrip().split(',')
        logging.debug(columns)

        # check if data missing in each column
        for x in range(len(header_title)):
            if columns[x] == '':
                column_empty_count[x] += 1

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
        
    # show some statistic
    logging.info('Total line: %d, processed: %d' % (line_count, processed_count))
    if column_empty_count and sum(column_empty_count) > 0:
        logging.info('Empty data column count:')
        for x in range(len(header_title)):
            if column_empty_count[x] > 0:
                logging.info('\t%s: %d.' % (header_title[x], column_empty_count[x]))

    fout.close()
    f.close()


if __name__ == '__main__':
    main()

