# -*- coding: utf-8 -*-
"""Scrape Daily Montreal ED Stats.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/12LSb0oph5R46iel_9p7Uijx1QNAvaa6x
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import argparse
import contextlib
import datetime
import os
import six
import sys
import time
import unicodedata
import dropbox
from datetime import date, timedelta


def upload(dbx, fullname, folder, subfolder, name, overwrite=False):
    """Upload a file.
    Return the request response, or None in case of error.
    """
    path = '/%s/%s/%s' % (folder, subfolder.replace(os.path.sep, '/'), name)
    while '//' in path:
        path = path.replace('//', '/')
    mode = (dropbox.files.WriteMode.overwrite
            if overwrite
            else dropbox.files.WriteMode.add)
    mtime = os.path.getmtime(fullname)
    with open(fullname, 'rb') as f:
        data = f.read()
    # with stopwatch('upload %d bytes' % len(data)):
    try:
        res = dbx.files_upload(
            data, path, mode,
            client_modified=datetime.datetime(*time.gmtime(mtime)[:6]),
            mute=True)
    except dropbox.exceptions.ApiError as err:
        print('*** API error', err)
        return None
    print('uploaded as', res.name.encode('utf8'))
    return res


def main():

    dropbox_api_key = os.environ['DROPBOX_ED_API']
    dbx = dropbox.Dropbox(dropbox_api_key)
    dbx.users_get_current_account()
    print('connected to dropbox')

    old_data_url = 'https://www.dropbox.com/s/w7n297w7pnapezn/dailyMontrealEdStats.csv?dl=1'
    old_data = pd.read_csv(old_data_url)
    old_data['date'] = pd.to_datetime(old_data['date'])
    print('old data: ', len(old_data), ' rows, ending ', old_data.date.max())

    url = 'https://santemontreal.qc.ca/fileadmin/fichiers_portail/Donnees_urgence/urgence_quotidien_media.html'
    r = requests.get(url)
    soup = BeautifulSoup(r.text)

    table = soup.find('table')

    rows = table.find_all('tr')
    table_rows = rows[0].find_all('tr')

    columns = [i.text.replace('-', '') for i in table_rows[6].find_all('td')]

    df_rows = []
    for tr in table_rows[7:][:-6]:
        td = tr.find_all('td')
        row = [i.text for i in td]
        if '\xa0' in str(tr):
            continue
        if 'Sous-total' in str(tr):
            continue
        df_rows.append(row)

    df = pd.DataFrame.from_records(df_rows, columns=columns)

    columns.remove('Installation')

    for int_col in columns:
        df[int_col] = pd.to_numeric(df[int_col], errors='coerce')

    yesterday = date.today() - timedelta(days=1)
    df['date'] = yesterday
    df.date = pd.to_datetime(df.date)

    new_data = df

    print('new data: ', len(new_data), ' rows, ending ', new_data.date.max())

    concat_data = pd.concat([old_data, new_data], ignore_index=False)
    concat_data = concat_data.drop_duplicates().reset_index(drop=True)
    print('concat data: ', len(concat_data), ' rows')

    concat_data.to_csv('dailyMontrealEdStats.csv', index=False)

    upload(dbx, 'dailyMontrealEdStats.csv', '', '',
           'dailyMontrealEdStats.csv', overwrite=True)