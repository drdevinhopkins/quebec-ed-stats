import streamlit as st
import pandas as pd
import pickle
from fbprophet import Prophet
from fbprophet.diagnostics import cross_validation
from datetime import datetime, timedelta
import requests
from datetime import date
import pytz
import urllib
import urllib.parse
import json
import plotly.graph_objects as go
from urllib.request import urlopen
import numpy as np
import pydeck as pdk


def main():
    st.title('Hourly ED Data')

    my_placeholder = st.empty()
    my_placeholder.text("Loading data...")

    old_data = pd.read_csv('data.csv')
    old_data['Mise_a_jour'] = pd.to_datetime(old_data['Mise_a_jour'])
    old_data["Heure_de_l'extraction_(image)"] = pd.to_datetime(
        old_data["Heure_de_l'extraction_(image)"])
    st.write(old_data)

    new_data = pd.read_csv(
        'https://www.msss.gouv.qc.ca/professionnels/statistiques/documents/urgences/Releve_horaire_urgences_7jours.csv', encoding="ISO-8859-1")

    new_data.rename(columns=lambda x: x.strip(), inplace=True)
    new_data['Mise_a_jour'] = pd.to_datetime(new_data['Mise_a_jour'])
    new_data["Heure_de_l'extraction_(image)"] = pd.to_datetime(
        new_data["Heure_de_l'extraction_(image)"])
    new_data['Nombre_de_civieres_fonctionnelles'] = pd.to_numeric(
        new_data['Nombre_de_civieres_fonctionnelles'], errors='coerce')
    new_data['Nombre_de_civieres_occupees'] = pd.to_numeric(
        new_data['Nombre_de_civieres_occupees'], errors='coerce')
    new_data['Nombre_de_patients_sur_civiere_plus_de_24_heures'] = pd.to_numeric(
        new_data['Nombre_de_patients_sur_civiere_plus_de_24_heures'], errors='coerce')
    new_data['Nombre_de_patients_sur_civiere_plus_de_48_heures'] = pd.to_numeric(
        new_data['Nombre_de_patients_sur_civiere_plus_de_48_heures'], errors='coerce')

    my_placeholder.text(" ")

    st.write(new_data)

    concat_data = pd.concat([old_data, new_data], ignore_index=False)

    st.write(concat_data)

    concat_data = concat_data.drop_duplicates().reset_index(drop=True)

    st.write(concat_data)

    concat_data.to_csv('data.csv', index=False)


if __name__ == "__main__":
    main()
