import datetime

from bs4 import BeautifulSoup
import pandas as pd
import requests

url = 'https://www.kusc.org/playlist/2019/08/03/'
headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:10.0) Gecko/20100101 Firefox/10.0'}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'lxml')

# tables are returned in reverse order on the page but actual chronological order
# pieces within tables are reverse chronological
t = soup.find_all('table')

# convert to dataframes
tables = pd.read_html(str(t))

# get shows and their hosts
accordions = soup.find_all('div', attrs={'class': 'accordion-content'})

for j in range(len(tables)):
    # add host and show name
    tables[j]['show'] = accordions[j].h3.contents[0].strip()
    tables[j]['host'] = accordions[j].h3.contents[1].text[5:]

    # extract purchase link for each piece
    # link in last <td> of each <tr>
    pieces = t[j].find_all('tr')
    links = [row.find_all('td')[-1].a.attrs['href'] for row in pieces]

    # add links as column
    tables[j]['purchase_link'] = links

df = pd.concat(tables, ignore_index=True)

del df['Buy CD']
df.rename(columns={'Unnamed: 0': 'time',
                   'Title': 'title',
                   'Composer': 'composer',
                   'Performers': 'performers',
                   'Record Co.Catalog No.': 'record_co_catalog_no',
                   }, inplace=True)

# clean up time and convert data type
df['time'] = df['time'].apply(lambda x: '0' + x if len(x) == 7 else x)
df['time'] = pd.to_datetime(df['time'], format='%I:%M %p').dt.time

# sort and drop dupes
df.sort_values(by='time', inplace=True)
df.drop_duplicates(inplace=True)

# insert date and datetime
today = datetime.date.today()
df.insert(0, 'date', today)
df.insert(0, 'datetime', df['time'].apply(lambda x: datetime.datetime.combine(today, x)))
