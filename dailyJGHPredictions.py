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

    retrieve_future_data(api_key='3d51d04f983a478e90f164916191012',
                         location_list=['Montreal'],
                         frequency=24, num_of_days=14,
                         location_label=False,
                         export_csv=True,
                         store_df=False)
    weather_forecast = pd.read_csv('Montreal-daily.csv')
    weather_forecast['ds'] = pd.to_datetime(weather_forecast['ds'])

    # dl=1 is important
    pickle_url = 'https://www.dropbox.com/s/ipj203q24sk0etp/jgh-prophet-daily.pkl?dl=1'
    import urllib.request
    u = urllib.request.urlopen(pickle_url)
    data = u.read()
    u.close()

    with open('jgh-prophet-daily.pkl', "wb") as f:
        f.write(data)

    with open('jgh-prophet-daily.pkl', 'rb') as f:
        m = pickle.load(f)

    forecast = m.predict(weather_forecast)

    date_string = datetime.now().date().strftime("%Y-%m-%d")
    new_predictions = forecast[['ds', 'yhat']]
    new_predictions.yhat = new_predictions.yhat.astype('int64')
    new_predictions = new_predictions.rename(columns={'yhat': date_string})
    new_predictions = new_predictions.set_index('ds')
    new_predictions = new_predictions.T

    old_predictions = pd.read_csv(
        'https://www.dropbox.com/s/8v2tnadtjpd5hht/jghPredictions.csv?dl=1', index_col=0)
    old_predictions.columns = pd.to_datetime(old_predictions.columns)

    predictions = pd.concat([old_predictions, new_predictions])
    predictions.to_csv('jghPredictions.csv')

    upload(dbx, 'jghPredictions.csv', '', '',
           'jghPredictions.csv', overwrite=True)


if __name__ == "__main__":
    main()
