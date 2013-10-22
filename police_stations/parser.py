#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging
import argparse
import subprocess
import requests


FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
ADDR_COUNTY_DATA_URL = 'http://download.post.gov.tw/post/download/county_h.csv'


def fix_addr(input_addr_string):

    output_addr_string = input_addr_string

    # change '臺' to '台' if it locates at 1st char in address
    if output_addr_string.find('臺') == 0:
        output_addr_string = output_addr_string.replace('臺', '台', 2)

    # other minor fixs (tuned for 1010611 data set)
    output_addr_string = output_addr_string.replace('南投縣鹿谷鎮', '南投縣鹿谷鄉')
    output_addr_string = output_addr_string.replace('屏東縣潮洲鎮', '屏東縣潮州鎮')
    output_addr_string = output_addr_string.replace('桃園縣楊梅鎮', '桃園縣楊梅市')
    if output_addr_string.startswith('苗栗市'):
        output_addr_string = output_addr_string.replace('苗栗市', '苗栗縣苗栗市')
    output_addr_string = output_addr_string.replace('高雄市茄定區', '高雄市茄萣區')
    output_addr_string = output_addr_string.replace('高雄市旗山里', '高雄市旗山區旗山里')
    output_addr_string = output_addr_string.replace('高雄高大寮區', '高雄市大寮區')
    output_addr_string = output_addr_string.replace('新竹市竹光路', '新竹市北區竹光路')
    output_addr_string = output_addr_string.replace('新竹縣竹南鎮', '苗栗縣竹南鎮')
    output_addr_string = output_addr_string.replace('嘉義市中山路', '嘉義市東區中山路')
    output_addr_string = output_addr_string.replace('嘉義市世賢路三段', '嘉義市西區世賢路三段')
    output_addr_string = output_addr_string.replace('嘉義市北港路', '嘉義市西區北港路')
    output_addr_string = output_addr_string.replace('嘉義市民族路', '嘉義市西區民族路')
    output_addr_string = output_addr_string.replace('嘉義市民權', '嘉義市東區民權')
    output_addr_string = output_addr_string.replace('嘉義市吳鳳南路', '嘉義市東區吳鳳南路')
    output_addr_string = output_addr_string.replace('嘉義市忠孝路', '嘉義市東區忠孝路')
    output_addr_string = output_addr_string.replace('嘉義市博愛路', '嘉義市西區博愛路')
    output_addr_string = output_addr_string.replace('台北市仁愛3段', '台北市大安區仁愛路三段')
    output_addr_string = output_addr_string.replace('台北市南京東路3段', '台北市松山區南京東路三段')
    output_addr_string = output_addr_string.replace('台東縣台東文化里市', '台東縣台東市文化里')
    output_addr_string = output_addr_string.replace('澎湖縣湖西村', '澎湖縣湖西鄉湖西村')
    output_addr_string = output_addr_string.replace('臺南市白河區白河里中正路128號', '臺南市白河區白河里中山路128號')
    output_addr_string = output_addr_string.replace('臺南市玉井區豊里村58號', '臺南市玉井區豐里村58號')
    output_addr_string = output_addr_string.replace('台南市左區區', '台南市左鎮區')
    output_addr_string = output_addr_string.replace('台南市台南市', '台南市')
    output_addr_string = output_addr_string.replace('台南市西區', '台南市中西區')

    # other fixs (tuned for 1020914 data set)
    output_addr_string = output_addr_string.replace('台東縣池上村', '台東縣池上鄉')

    return output_addr_string

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

    county_data_available = False
    # collect address county/city and township data
    r = requests.get(ADDR_COUNTY_DATA_URL)
    if r.status_code == 200:
        county_list = []
        big5_csv = r.content
        utf8_csv = big5_csv.decode('big5').encode('utf8')
        line_list = utf8_csv.splitlines()
        for line in line_list:
            columns = line.split(',')
            county_list.append(columns[1])
        county_data_available = True
    else:
        logging.warning('Address county city data is not available.')

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
    suspicious_addr = 0

    # processed line by line
    for line in f:

        line_count = line_count + 1

        # The 1st line is always the header line, just record the column title and skip processing
        if line_count == 1:
            header_title = line.rstrip().split(',')
            column_empty_count = [0] * len(header_title)
            try:
                COL_NAME = header_title.index('單位')
            except ValueError:
                COL_NAME = -1
            try:
                COL_PHONE = header_title.index('電話')
            except ValueError:
                COL_PHONE = -1
            try:
                COL_ADDR = header_title.index('地址')
            except ValueError:
                COL_ADDR = -1
            try:
                COL_X = header_title.index('FLOOR_X')
            except ValueError:
                COL_X = -1
            try:
                COL_Y = header_title.index('FLOOR_Y')
            except ValueError:
                COL_Y = -1
            continue

        # real data column
        columns = line.rstrip().split(',')

        # fix address
        if COL_ADDR >= 0:
            columns[COL_ADDR] = fix_addr(columns[COL_ADDR])

        # check if data missing in each column
        for x in range(len(header_title)):
            if columns[x] == '':
                column_empty_count[x] += 1

        # collect necessory columns only
        updated_line = ''
        for col in [COL_NAME, COL_PHONE, COL_ADDR, COL_X, COL_Y]:
            if col >= 0:
                if len(updated_line) > 0:
                    updated_line += ',' + columns[col]
                else:
                    updated_line += columns[col]

        # generate county/city, and town
        if COL_ADDR >= 0:
            strAddr = columns[COL_ADDR]
            if county_data_available:
                found = False
                for county in county_list:
                    if strAddr.startswith(county):
                        found = True
                        break
                if not found:
                    suspicious_addr += 1
                    logging.warning('[%d]Addr(%s) may not be completed!' % (suspicious_addr, strAddr))
            head, sep, tail = strAddr.partition('縣')
            if sep and tail:
                county_city = head + sep

                strRestAddr = tail
                head, sep, tail = strRestAddr.partition('市')
                if sep and tail:
                    town = head + sep
                else:
                    head, sep, tail = strRestAddr.partition('鄉')
                    if sep and tail:
                        town = head + sep
                    else:
                        head, sep, tail = strRestAddr.partition('鎮')
                        if sep and tail:
                            town = head + sep
                        else:
                            town = ''
            else:
                head, sep, tail = strAddr.partition('市')
                if sep and tail:
                    county_city = head + sep

                    strRestAddr = tail
                    head, sep, tail = strRestAddr.partition('區')
                    if sep and tail:
                        town = head + sep
                    else:
                        town = ''
                else:
                    county_city = ''
                    town = ''
                    logging.warning('No county/city in address: %s' % strAddr)
        else:
            county_city = ''
            town = ''

        logging.debug('County/City = %s, Town = %s' % (county_city, town))
        updated_line += ',' + county_city + ',' + town

        # convert TWD97 TM2 (x,y) to WGS84 (lat,lng)
        if COL_X >= 0 and COL_Y >= 0 and len(columns[COL_X]) > 0 and len(columns[COL_Y]) > 0:
            p = subprocess.Popen(
                ['proj', '-I', '+proj=tmerc', '+lat_0=0', '+lon_0=121',
                '+x_0=250000', '+y_0=0', '+k=0.9999', '+ellps=WGS84',
                '-f', '%.6f', '-s'], stdin=subprocess.PIPE,
                stdout=subprocess.PIPE)
            out = p.communicate(columns[COL_X] + ' ' + columns[COL_Y])[0]
            p.stdout.close()
            latlng = out.rstrip().split('\t')
            updated_line += ',' + latlng[0] + ',' + latlng[1]
        else:
            logging.warning('No x and/or y in TWD97 format coordinations')
            updated_line += ',,'

        # write back processed line
        fout.write(updated_line + '\n')

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

