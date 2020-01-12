import os
import datetime

import pandas as pd
from sqlalchemy import create_engine

from utils import get_date_list, get_soup, extract_soup_data, process_dataframes, clean_and_format_dataframe
from playlist_types import playlist_types

basdir = os.path.abspath(os.path.dirname(__file__))
engine = create_engine(os.environ.get('DATABASE_URL') or f'sqlite:///{os.path.join(basdir, "app.sqlite")}')

dates = get_date_list()
query_date = '2019/08/03'

for query_date in dates:
    soup = get_soup(query_date)

    tables_html, tables_dfs, accordions = extract_soup_data(soup)

    tables_dfs = process_dataframes(tables_html, tables_dfs, accordions)

    # make one df from all the shows
    df = pd.concat(tables_dfs, ignore_index=True)

    del df['Buy CD']
    df.rename(columns={'Unnamed: 0': 'time',
                       'Title': 'title',
                       'Composer': 'composer',
                       'Performers': 'performers',
                       'Record Co.Catalog No.': 'record_co_catalog_no',
                       }, inplace=True)

    df = clean_and_format_dataframe(df, datetime.datetime.strptime(query_date, '%Y/%m/%d'))

    df.to_sql('playlist', engine, if_exists='append', index=False, dtype=playlist_types)
