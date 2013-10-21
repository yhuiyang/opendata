#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import argparse
import requests


FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
DATA_SRC_URL = 'http://download.post.gov.tw/post/download/county_h.csv'


# command line arguments
parser = argparse.ArgumentParser(\
    description='''
Download county/city and township/dist data and save to file''',
    epilog='Feel free to reuse, reproduction and/or redistribution.')
parser.add_argument('-v', '--verbose', help='Enable more debug message', action='count')
parser.add_argument('-o', '--output', help='Output file name.', metavar='filename', default='CountyCityTownship.tbl')
args = parser.parse_args()
if args.verbose:
    logging.basicConfig(level=logging.DEBUG, format=FORMAT, datefmt=DATE_FORMAT)
else:
    logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt=DATE_FORMAT)


# load from url
r = requests.get(DATA_SRC_URL)
if r.status_code == 200:
    fout = open(args.output, 'w')
    csv = r.content
    utf8_csv = csv.decode('big5').encode('utf8')
    line_list = utf8_csv.splitlines()
    for line in line_list:
        columns = line.split(',')
        county_city_township = columns[1]
        
        head, sep, tail = county_city_township.partition('縣')
        if sep and tail:
            county_city = head + sep
            township = tail
        else:
            head, sep, tail = county_city_township.partition('市')
            if sep and tail:
                county_city = head + sep
                township = tail
            else:
                logging.warning('Skipped county/city: %s' % county_city_township)
                continue

        fout.write(county_city + ' ' + township + '\n')
    fout.close()
else:
    logging.error('Failed to get source data. Maybe try it later...!?')

