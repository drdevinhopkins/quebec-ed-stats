import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly as py
from datetime import *
from streamlit import caching


def main():

    caching.clear_cache()

    @st.cache
    def load_data():
        # quebec_data = pd.read_csv(
        #     'https://www.dropbox.com/s/7idv6buofuqru5z/hourlyQuebecEDStats.csv?dl=1')
        # mtl_data = pd.read_csv(
        #     'https://www.dropbox.com/s/w7n297w7pnapezn/dailyMontrealEdStats.csv?dl=1')
        jgh_data = pd.read_csv(
            'https://www.dropbox.com/s/keafvwlkboedkdm/jghDailyVisits.csv?dl=1')
        jgh_data.ds = pd.to_datetime(jgh_data.ds)
        jgh_data = jgh_data.set_index('ds')
        daily_JGH_predictions_df = pd.read_csv(
            'https://www.dropbox.com/s/8v2tnadtjpd5hht/jghPredictions.csv?dl=1', index_col=0)
        daily_JGH_predictions_df.index = pd.to_datetime(
            daily_JGH_predictions_df.index)
        daily_JGH_predictions_df.columns = pd.to_datetime(
            daily_JGH_predictions_df.columns)
        daily_JGH_predictions_df_archive = daily_JGH_predictions_df
        daily_JGH_predictions_df = daily_JGH_predictions_df.tail(1).T
        daily_JGH_predictions_df = daily_JGH_predictions_df.rename(
            columns={daily_JGH_predictions_df.columns[0]: "y"})
        prediction_archive_dates = [date for date in list(
            daily_JGH_predictions_df_archive) if date < datetime.now().date()]
        prediction_archive_visits = [int(
            daily_JGH_predictions_df_archive.loc[date][date]) for date in prediction_archive_dates]

        old_JGH_daily = pd.read_csv(
            'https://www.dropbox.com/s/keafvwlkboedkdm/jghDailyVisits.csv?dl=1')
        old_JGH_daily.ds = pd.to_datetime(old_JGH_daily.ds)
        old_JGH_daily = old_JGH_daily.tail(14)
        old_JGH_daily = old_JGH_daily.set_index('ds')

        # return quebec_data, mtl_data, jgh_data, daily_JGH_predictions_df, old_JGH_daily, prediction_archive_dates, prediction_archive_visits, daily_JGH_predictions_df_archive
        return jgh_data, daily_JGH_predictions_df, old_JGH_daily, prediction_archive_dates, prediction_archive_visits, daily_JGH_predictions_df_archive

    my_placeholder = st.empty()
    my_placeholder.text("Loading data...")
    # quebec_data, mtl_data, jgh_data, daily_JGH_predictions_df, old_JGH_daily, prediction_archive_dates, prediction_archive_visits, daily_JGH_predictions_df_archive = load_data()
    jgh_data, daily_JGH_predictions_df, old_JGH_daily, prediction_archive_dates, prediction_archive_visits, daily_JGH_predictions_df_archive = load_data()

    my_placeholder.text(" ")

    st.title('JGH Predictions')

    today_string = datetime.now().date().strftime("%Y-%m-%d")

    fig = go.Figure()
    fig.update_layout(title_text="JGH Visits",
                      title_font_size=18)
    fig.add_trace(go.Scatter(x=daily_JGH_predictions_df.index, y=daily_JGH_predictions_df.y.to_list(), mode='lines+markers',
                             name='Predictions', showlegend=True))
    fig.add_trace(go.Scatter(x=old_JGH_daily.index, y=old_JGH_daily.y.to_list(), mode='lines+markers',
                             name='Daily Visits', showlegend=True))

    prediction_archive_dates = [date for date in list(
        daily_JGH_predictions_df_archive) if date <= jgh_data.index.max()]
    prediction_archive_visits = [int(
        daily_JGH_predictions_df_archive.loc[date][date]) for date in prediction_archive_dates]
    actual_visits = [int(jgh_data.loc[date]['y'])
                     for date in prediction_archive_dates]
    predictions = pd.DataFrame(prediction_archive_visits, columns=['yhat'])
    predictions['y'] = actual_visits
    predictions['ds'] = prediction_archive_dates
    predictions['abs_diff'] = abs(
        predictions.y - predictions.yhat) / predictions.y
    mape = predictions.abs_diff.mean()
    mape = round(mape * 100, 2)

    fig.add_trace(go.Scatter(x=prediction_archive_dates, y=prediction_archive_visits, mode='lines+markers',
                             name='Previous Predictions', showlegend=True))
    st.plotly_chart(fig)

    st.write('Mean Absolute Percentage Error (MAPE): '+str(mape)+'%')

    # st.title('Quebec ED Data')

    # st.subheader('Quebec')
    # st.write(quebec_data)

    # select_hospital = st.selectbox(
    #     'Choose a hospital:',
    #     quebec_data['Nom_installation'].unique())

    # st.write(quebec_data[quebec_data['Nom_installation'] == select_hospital])

    # st.subheader('Montreal')
    # st.write(mtl_data)

    # st.subheader('JGH')
    # st.write(jgh_data)

    # st.line_chart(jgh_data)


if __name__ == "__main__":
    main()
