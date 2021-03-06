# -*- coding: utf-8 -*-
"""Updating QC Covid Projections.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1AMtjn5EKFGhZ_R33Jn-NzUPYzKe6YPKH
"""


def load_qc_data():
    import pandas as pd
    qc_data = pd.read_csv(
        'https://www.dropbox.com/s/ud7r3l20mzyllvm/qc-covid-stats.csv?dl=1')
    qc_data.date = pd.to_datetime(qc_data.date)
    qc_data.total_cases = pd.to_numeric(
        qc_data.total_cases, errors='coerce')
    qc_data.total_deaths = pd.to_numeric(
        qc_data.total_deaths, errors='coerce')
    qc_data.hospitalizations = pd.to_numeric(
        qc_data.hospitalizations, errors='coerce')
    qc_data.icu = pd.to_numeric(qc_data.icu, errors='coerce')
    qc_data.total_recovered = pd.to_numeric(
        qc_data.total_recovered, errors='coerce')
    qc_data.under_investigation = pd.to_numeric(
        qc_data.under_investigation, errors='coerce')

    death_predictions = pd.read_csv(
        'https://www.dropbox.com/s/xqahiruvf7ghykp/deaths.csv?dl=1')
    death_predictions.date = pd.to_datetime(death_predictions.date)

    target_date = qc_data.set_index('date').iloc[-1].name
    severity_index = (qc_data.set_index('date').iloc[-1].total_deaths-death_predictions.set_index('date').loc[target_date].optimistic)/(
        death_predictions.set_index('date').loc[target_date].pessimistic-death_predictions.set_index('date').loc[target_date].optimistic)

    return qc_data, severity_index


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
    qc_data, severity_index = load_qc_data()

    df = qc_data[['date', 'total_cases']].copy()
    df.rename({'date': 'ds', 'total_cases': 'y'}, axis=1, inplace=True)
    # df.tail()

    from fbprophet import Prophet

    optimistic_cap = 30000
    pessimistic_cap = 67000
    realistic_cap = severity_index * \
        (pessimistic_cap-optimistic_cap) + optimistic_cap

    optimistic_df = df.copy()
    optimistic_df['cap'] = optimistic_cap

    pessimistic_df = df.copy()
    pessimistic_df['cap'] = pessimistic_cap

    realistic_df = df.copy()
    realistic_df['cap'] = realistic_cap

    m_optimistic = Prophet(growth="logistic")
    m_pessimistic = Prophet(growth="logistic")
    m_realistic = Prophet(growth="logistic")

    m_optimistic.fit(optimistic_df)
    m_pessimistic.fit(pessimistic_df)
    m_realistic.fit(realistic_df)

    future_optimistic = m_optimistic.make_future_dataframe(periods=30)
    future_pessimistic = m_pessimistic.make_future_dataframe(periods=30)
    future_realistic = m_realistic.make_future_dataframe(periods=30)

    future_optimistic['cap'] = optimistic_df['cap'].iloc[0]
    future_pessimistic['cap'] = pessimistic_df['cap'].iloc[0]
    future_realistic['cap'] = realistic_df['cap'].iloc[0]

    forecast_optimistic = m_optimistic.predict(future_optimistic)
    forecast_pessimistic = m_pessimistic.predict(future_pessimistic)
    forecast_realistic = m_realistic.predict(future_realistic)

    from datetime import date
    today = pd.to_datetime(date.today())

    forecast_realistic[forecast_realistic.ds > today][['ds', 'yhat']].rename(
        {'ds': 'date', 'yhat': 'total_cases'}, axis=1).reset_index(drop=True).to_csv('forecast_realistic.csv', index=False)
    forecast_optimistic[forecast_optimistic.ds > today][['ds', 'yhat']].rename(
        {'ds': 'date', 'yhat': 'total_cases'}, axis=1).reset_index(drop=True).to_csv('forecast_optimistic.csv', index=False)
    forecast_pessimistic[forecast_pessimistic.ds > today][['ds', 'yhat']].rename(
        {'ds': 'date', 'yhat': 'total_cases'}, axis=1).reset_index(drop=True).to_csv('forecast_pessimistic.csv', index=False)

    upload('forecast_realistic.csv', '', '',
           'forecast_realistic.csv', overwrite=True)
    upload('forecast_optimistic.csv', '', '',
           'forecast_optimistic.csv', overwrite=True)
    upload('forecast_pessimistic.csv', '', '',
           'forecast_pessimistic.csv', overwrite=True)


if __name__ == "__main__":
    main()
