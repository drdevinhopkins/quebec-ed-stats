import streamlit as st
import pandas as pd


def main():

    @st.cache
    def load_data():
        quebec_data = pd.read_csv(
            'https://www.dropbox.com/s/7idv6buofuqru5z/hourlyQuebecEDStats.csv?dl=1')
        mtl_data = pd.read_csv(
            'https://www.dropbox.com/s/w7n297w7pnapezn/dailyMontrealEdStats.csv?dl=1')
        jgh_data = pd.read_csv(
            'https://www.dropbox.com/s/keafvwlkboedkdm/jghDailyVisits.csv?dl=1')
        return quebec_data, mtl_data, jgh_data

    st.title('Quebec ED Data')

    my_placeholder = st.empty()
    my_placeholder.text("Loading data...")
    quebec_data, mtl_data, jgh_data = load_data()

    my_placeholder.text(" ")

    st.subheader('Quebec')
    st.write(quebec_data)

    select_hospital = st.selectbox(
        'Which number do you like best?',
        quebec_data['Nom_installation'].unique())

    st.write(quebec_data[quebec_data['Nom_installation'] == select_hospital])

    st.subheader('Montreal')
    st.write(mtl_data)

    st.subheader('JGH')
    jgh_data = jgh_data.set_index('ds')
    st.write(jgh_data)

    st.line_chart(jgh_data)


if __name__ == "__main__":
    main()
