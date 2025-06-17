import os
import requests
import pandas as pd
from pathlib import Path

API_URL = "https://www.geoboundaries.org/api/current/gbOpen/ALL/ADM1/"
resp = requests.get(API_URL, timeout=15)
resp.raise_for_status()
countries_response = resp.json()

# Pasamos a DataFrame
df = pd.DataFrame(countries_response)

# Seleccionamos sólo las columnas que necesitamos
countries = df[['boundaryName', 'boundaryISO', 'Continent']]
continents = df['Continent'].unique()