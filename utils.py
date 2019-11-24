import datetime
import sys
from typing import List

import pandas as pd
import requests
from bs4 import BeautifulSoup
from bs4.element import ResultSet


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


def process_dataframes(html: ResultSet,
                       table_dataframes: List[pd.DataFrame],
                       hosts_and_shows: ResultSet) -> List[pd.DataFrame]:
    for j in range(len(table_dataframes)):
        # add host and show name
        table_dataframes[j]['show'] = hosts_and_shows[j].h3.contents[0].strip()
        table_dataframes[j]['host'] = hosts_and_shows[j].h3.contents[1].text[5:]

        # extract purchase link for each piece: last <td> of each <tr>
        pieces = html[j].find_all('tr')
        links = [row.find_all('td')[-1].a.attrs['href'] for row in pieces]

        # add links as column
        table_dataframes[j]['purchase_link'] = links

        return table_dataframes


def clean_and_format_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    # clean time and convert data type
    dataframe['time'] = dataframe['time'].apply(lambda x: '0' + x if len(x) == 7 else x)
    dataframe['time'] = pd.to_datetime(dataframe['time'], format='%I:%M %p').dt.time

    # make datetime and time columns tz-aware

    # sort and drop dupes
    dataframe.sort_values(by='time', inplace=True)
    dataframe.drop_duplicates(inplace=True)

    # insert date and datetime
    today = datetime.date.today()
    dataframe.insert(0, 'date', today)
    dataframe.insert(0, 'datetime', dataframe['time'].apply(lambda x: datetime.datetime.combine(today, x)))

    return dataframe
