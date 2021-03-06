# -*- coding: utf-8 -*-
"""Scraping QC Covid Stats with Selenium.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1S8Axmjbaq3pKM5Tk-rO3ngP9H1ICRqmD
"""


def upload(fullname, folder, subfolder, name, overwrite=False):
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
    # from datetime import date, timedelta

    dropbox_api_key = os.environ['DROPBOX_ED_API']
    dbx = dropbox.Dropbox(
        dropbox_api_key)
    dbx.users_get_current_account()
    print('connected to dropbox')

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
    import pandas as pd
    from selenium import webdriver
    import os
    import datetime

    print('loading chrome webdriver')
    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    wd = webdriver.Chrome(executable_path=os.environ.get(
        "CHROMEDRIVER_PATH"), chrome_options=chrome_options)

    print('accessing data')
    wd.get("https://www.inspq.qc.ca/covid-19/donnees")

    results = wd.find_elements_by_xpath(
        "/html/body/div[2]/div/div[3]/main/div/section/div/div/article/div/div[2]/div/div/div[1]/div")

    if len(results) > 0:
        print('successfully accessed data')

    raw_results_list = results[0].text.split('\n')
    total_cases = int(raw_results_list[0].replace(" ", ""))
    total_deaths = int(raw_results_list[2].replace(" ", ""))
    hospitalizations = int(raw_results_list[4].replace(" ", ""))
    icu = int(raw_results_list[6].replace(" ", ""))
    total_recovered = int(raw_results_list[8].replace(" ", ""))
    under_investigation = int(raw_results_list[10].replace(" ", ""))

    print('quitting webdriver')
    wd.quit()

    print('accessing old data')
    old_data_url = 'https://www.dropbox.com/s/ud7r3l20mzyllvm/qc-covid-stats.csv?dl=1'
    old_df = pd.read_csv(old_data_url)
    old_df['date'] = pd.to_datetime(old_df['date'])

    print('adding new data')
    new_df = old_df.append({'date': pd.to_datetime(datetime.date.today()), 'total_cases': total_cases, 'total_deaths': total_deaths,
                            'hospitalizations': hospitalizations, 'icu': icu, 'total_recovered': total_recovered, 'under_investigation': under_investigation}, ignore_index=True)
    new_df = new_df.set_index('date').drop_duplicates(
        keep='first').reset_index()
    new_df.to_csv('qc-covid-stats.csv', index=False)

    if not(new_df.equals(old_df)):
        upload('qc-covid-stats.csv', '', '',
               'qc-covid-stats.csv', overwrite=True)
    else:
        print('no new data')


if __name__ == "__main__":
    main()
