import os

import pandas as pd
from sqlalchemy import create_engine

from utils import get_date_list, get_soup, extract_soup_data, process_dataframes, clean_and_format_dataframe
from playlist_types import playlist_types

engine = create_engine(os.environ['DATABASE_URL'])

dates = get_date_list()

for date in dates:
    soup = get_soup(date)

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

    df = clean_and_format_dataframe(df)

    df.to_sql('playlist', engine, if_exists='append', index=False, dtype=playlist_types)
