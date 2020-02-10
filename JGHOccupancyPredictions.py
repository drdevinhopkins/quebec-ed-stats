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
    weather_api_key = os.environ['WEATHER_API']
    dropbox_api_key = os.environ['DROPBOX_ED_API']
    dbx = dropbox.Dropbox(dropbox_api_key)
    dbx.users_get_current_account()
    print('connected to dropbox')

    hist_data = pd.read_csv(
        'https://www.dropbox.com/s/fqsdx1ovqsljwqa/jghOccupancy.csv?dl=1')
    hist_data.ds = pd.to_datetime(hist_data.ds)

    retrieve_future_data(api_key=weather_api_key,
                         location_list=['Montreal'],
                         frequency=1, num_of_days=5,
                         location_label=False,
                         export_csv=True,
                         store_df=False)
    weather_forecast = pd.read_csv('Montreal-hourly.csv')
    weather_forecast['ds'] = pd.to_datetime(weather_forecast['ds'])
    weather_forecast = weather_forecast[weather_forecast.ds > hist_data.ds.max(
    )]

    pickle_url = 'https://www.dropbox.com/s/7jz0ardm7wy77xl/jgh-prophet-occupancy.pkl?dl=1'
    import urllib.request
    u = urllib.request.urlopen(pickle_url)
    data = u.read()
    u.close()

    with open('jgh-prophet-occupancy.pkl', "wb") as f:
        f.write(data)

    with open('jgh-prophet-occupancy.pkl', 'rb') as f:
        m = pickle.load(f)

    forecast = m.predict(weather_forecast)

    forecast[['ds', 'yhat']].to_csv('JGHOccupancyPredictions.csv', index=False)
    hist_data.tail(72).to_csv('JGHOccupancyLast72hrs.csv', index=False)

    upload(dbx, 'JGHOccupancyPredictions.csv', '', '',
           'JGHOccupancyPredictions.csv', overwrite=True)
    upload(dbx, 'JGHOccupancyLast72hrs.csv', '', '',
           'JGHOccupancyLast72hrs.csv', overwrite=True)


if __name__ == "__main__":
    main()
