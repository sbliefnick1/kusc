import datetime
import json
import re
import sys
from typing import List

import pandas as pd
import requests
from bs4 import BeautifulSoup
from bs4.element import ResultSet, Tag, NavigableString

# include re.IGNORECASE flag
composition_types = ['adagio',
                     'allegro',
                     'andante',
                     'barcarolle',
                     'capriccio',
                     'concertino',
                     'concerto grosso',
                     'concerto',
                     'divertimento',
                     'dances?',
                     'etudes?',
                     'fantasia',
                     'fantasy',
                     'finale',
                     'gigue',
                     'interlude',
                     'intermezzo',
                     'lullaby',
                     'meditation',
                     'minuet',
                     'motet',
                     'nocturne',
                     'overture',
                     'passacaille',
                     'pastorale',
                     'polka',
                     'prelude',
                     'rhapsody',
                     'romance',
                     'rondeau',
                     'rondo',
                     'scenes?',
                     'scherzando',
                     'scherzo',
                     'selection?',
                     'serenade',
                     'sinfonia',
                     'sonata',
                     'sonatina',
                     'study'
                     'suite',
                     'symphonie',
                     'symphony',
                     'theme',
                     'valse',
                     'variation?',
                     'waltz',
                     ]

comps = re.compile(rf'\b(?:{"|".join(composition_types)})\b', re.I)


def get_date_list() -> list:
    # check command line args
    args = sys.argv
    if len(args) > 1:
        date_list = list(args[1:])
    # if none then get yesterday's date
    else:
        date_list = list()
        date_list.append((datetime.datetime.today() - datetime.timedelta(days=1)).strftime('%Y/%m/%d'))

    return date_list


def get_soup(query_date: str) -> BeautifulSoup:
    base_url = 'https://www.kusc.org/playlist/'
    test_url = f'{base_url}{query_date}/'
    # TODO: swap `test_url` and `url` and remove `test_url`
    url = 'https://www.kusc.org/playlist/2019/08/03/'
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:10.0) Gecko/20100101 Firefox/10.0'}
    response = requests.get(url, headers=headers)
    return BeautifulSoup(response.text, 'lxml')


def extract_soup_data(soup_data: BeautifulSoup) -> (ResultSet, List[pd.DataFrame], ResultSet):
    # tables are returned in reverse order on the page but actual chronological order
    # pieces within tables are reverse chronological
    html = soup_data.find_all('table')

    # convert to dataframes
    table_dataframes = pd.read_html(str(html))

    # get shows and their hosts
    hosts_and_shows = soup_data.find_all('div', attrs={'class': 'accordion-content'})

    return html, table_dataframes, hosts_and_shows


def strip_performer_info(table: Tag) -> List[List[str]]:
    # performers are in the third <td> of every row (time is stored in a <th>)
    performers = [tr.find_all('td')[2].contents for tr in table.find_all('tr')]
    # remove <br>s and strip whitespace
    return [[item.strip() for item in p if type(item) is NavigableString] for p in performers]


def split_performer_strings(performer: List[str]) -> dict:
    info = {}
    for p in performer:
        # soloist(s), e.g., 'John Smith, clarinet'
        if re.match(r'.+, [a-z]+', p):
            soloists = p.split('; ')
            info['soloist'] = [{'musician': s.split(', ')[0], 'instrument': s.split(', ')[1]} for s in soloists]
        # conductor / ensemble
        elif re.match(r'.+ / .+', p):
            info['conductor'], info['ensemble'] = p.split(' / ')
        # ensemble only
        elif p:
            info['ensemble'] = p
        # else:
        #     info = None

    return json.dumps(info)


def determine_composition_type(title):
    comp = re.search(comps, title)
    if comp:
        return comp.group()
    return


def process_dataframes(html: ResultSet,
                       table_dataframes: List[pd.DataFrame],
                       hosts_and_shows: ResultSet) -> List[pd.DataFrame]:
    for j in range(len(table_dataframes)):
        # add host and show name
        table_dataframes[j]['show'] = hosts_and_shows[j].h3.contents[0].strip()
        table_dataframes[j]['host'] = hosts_and_shows[j].h3.contents[1].text[5:]

        # extract performer information: third <td> of each <tr>
        performers_cleaned = strip_performer_info(html[j])
        performers = [split_performer_strings(p) for p in performers_cleaned]
        table_dataframes[j]['Performers'] = performers

        # todo: determine type of piece, e.g., concerto, ballad, sonata by extracting from title
        table_dataframes[j]['composition_type'] = table_dataframes[j]['Title'].apply(determine_composition_type)

        # extract purchase link for each piece: last <td> of each <tr>
        pieces = html[j].find_all('tr')
        links = [row.find_all('td')[-1].a.attrs['href'] for row in pieces]

        # add links as column
        table_dataframes[j]['purchase_link'] = links

    return table_dataframes


def clean_and_format_dataframe(dataframe: pd.DataFrame, query_date: datetime.date) -> pd.DataFrame:
    # clean time and convert data type
    dataframe['time'] = dataframe['time'].apply(lambda x: '0' + x if len(x) == 7 else x)
    dataframe.insert(0, 'air_time', pd.to_datetime(dataframe['time'], format='%I:%M %p').dt.time)
    del dataframe['time']

    # TODO: make datetime and time columns tz-aware

    # sort and drop dupes
    dataframe.sort_values(by='air_time', inplace=True)
    dataframe.drop_duplicates(inplace=True)

    # insert date and datetime
    dataframe.insert(0, 'air_date', query_date)
    dataframe.insert(0, 'air_datetime', dataframe['air_time'].apply(lambda x: datetime.datetime.combine(query_date, x)))

    return dataframe
