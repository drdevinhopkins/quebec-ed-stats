import pandas as pd
import numpy as np
import pickle
from fbprophet import Prophet
import urllib
import urllib.parse
import json
import plotly.graph_objects as go
from urllib.request import urlopen
from weather import *
import dropbox
from dropboxUtils import *
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
from datetime import *
from wwo_hist import retrieve_hist_data
import pytz


def main():

    dropbox_api_key = os.environ['DROPBOX_ED_API']
    dbx = dropbox.Dropbox(dropbox_api_key)
    dbx.users_get_current_account()
    print('connected to dropbox')

    df = pd.read_csv(
        'https://www.dropbox.com/s/keafvwlkboedkdm/jghDailyVisits.csv?dl=1')
    df.ds = pd.to_datetime(df.ds)
    print('jgh daily visits loaded')

    stat_days_df = pd.read_excel(
        'https://www.dropbox.com/s/yghzalce8gy7x92/jghStatDays.xlsx?dl=1')

    ramq_stat_days = stat_days_df['RAMQ']
    ramq_stat_days = ramq_stat_days.dropna()
    jgh_stat_days = stat_days_df['JGH']
    jgh_stat_days = jgh_stat_days.dropna()
    ramq_stat_days = pd.DataFrame({
        'holiday': 'ramq',
        'ds': ramq_stat_days.to_list(),
        'lower_window': 0,
        'upper_window': 1,
    })
    jgh_stat_days = pd.DataFrame({
        'holiday': 'jgh',
        'ds': jgh_stat_days.to_list(),
        'lower_window': 0,
        'upper_window': 1,
    })
    holidays = pd.concat((ramq_stat_days, jgh_stat_days))
    print('stat days prepared')

    # Get all Montreal Canadiens games in our time frame (2012-present) from the NHL's REST API
    hockey_df = pd.read_csv(
        'https://www.dropbox.com/s/g00ih64ndksshwr/montrealHockey.csv?dl=1')
    hockey_df.dateTime = pd.to_datetime(hockey_df.dateTime)

    # Separate the games by Home or Away
    home_hockey_df = hockey_df[hockey_df['homeTeam'] == 'Montreal Canadiens']

    away_hockey_df = hockey_df[hockey_df['awayTeam'] == "Montreal Canadiens"]

    # Format them as Prophet expects
    home_hockey = pd.DataFrame({
        'holiday': 'homeHockey',
        'ds': pd.to_datetime(home_hockey_df['dateTime']),
        'lower_window': 0,
        'upper_window': 1,
    })

    away_hockey = pd.DataFrame({
        'holiday': 'awayHockey',
        'ds': pd.to_datetime(away_hockey_df['dateTime']),
        'lower_window': 0,
        'upper_window': 1,
    })

    # Add the hockey games to our stat day data
    holidays = pd.concat(
        (home_hockey, away_hockey, ramq_stat_days, jgh_stat_days))
    print('hockey games added')

    # Load our weather data from Dropbox
    weather_df = pd.read_csv(
        'https://www.dropbox.com/s/688u8aw6k0eqzqb/montrealDailyWeather.csv?dl=1')
    weather_df['ds'] = pd.to_datetime(weather_df['ds'])
    print('old weather added')

    # Fetch whicher days are missing, and 2 days into the future (weather forecast), which is the maximum the WWO API let's us access through the this API
    # The Data is saved as a csv file called 'Montreal'
    frequency = 24
    start_date = (weather_df.ds.max()-timedelta(days=20)
                  ).date().strftime("%d-%b-%Y").upper()
    end_date = (datetime.now(pytz.utc)).astimezone(
        pytz.timezone('US/Eastern')).date().strftime("%d-%b-%Y").upper()
    api_key = '3d51d04f983a478e90f164916191012'
    location_list = ['Montreal']
    retrieve_hist_data(api_key,
                       location_list,
                       start_date,
                       end_date,
                       frequency,
                       location_label=False,
                       export_csv=True,
                       store_df=False)

    missing_weather_df = pd.read_csv('Montreal.csv')
    missing_weather_df['date_time'] = pd.to_datetime(
        missing_weather_df['date_time'])
    missing_weather_df = missing_weather_df.drop(
        ['moonrise', 'moonset', 'sunrise', 'sunset'], axis=1)
    missing_weather_df = missing_weather_df.rename(columns={"date_time": "ds"})
    print('new weather fetched')

    # Concatenate the old weather data with the missing weather data
    final_weather_df = pd.concat([weather_df, missing_weather_df])
    final_weather_df.tail(14)

    final_weather_df.to_csv('montrealDailyWeather.csv', index=False)

    upload(dbx, 'montrealDailyWeather.csv', '', '',
           'montrealDailyWeather.csv', overwrite=True)

    regressors = final_weather_df.columns.to_list()
    regressors.remove('ds')

    df.ds = pd.to_datetime(df.ds)
    final_df = pd.merge(df, final_weather_df, on='ds')

    print('starting to build model')
    # Instantiate our model with our stat day and hockey variables saved in the 'holidays' dataframe
    m = Prophet(holidays=holidays, seasonality_mode='multiplicative',
                changepoint_prior_scale=0.5, changepoint_range=0.85)
    # Add Prophet's built-in holidays for Canada
    m.add_country_holidays(country_name='CA')
    # Add our 20 weather variables as regressors
    for regressor in regressors:
        m.add_regressor(regressor)
    # Fit our model to our data
    # m.fit(final_df)
    # Fit our model to data from before 2019
    m.fit(final_df)
    print('finished fitting model')

    import pickle
    pkl_path = "jgh-prophet-daily.pkl"
    with open(pkl_path, "wb") as f:
        # Pickle the 'Prophet' model using the highest protocol available.
        pickle.dump(m, f)

    upload(dbx, 'jgh-prophet-daily.pkl', '', '',
           'jgh-prophet-daily.pkl', overwrite=True)


if __name__ == "__main__":
    main()