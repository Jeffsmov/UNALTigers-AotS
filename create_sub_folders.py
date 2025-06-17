import requests
import pandas as pd
import os


API_URL = "https://www.geoboundaries.org/api/current/gbOpen/ALL/ADM1/"
resp = requests.get(API_URL, timeout=15)
resp.raise_for_status()
countries_response = resp.json()

df = pd.DataFrame(countries_response)
continents = df['Continent'].unique()
countries = df[['boundary']]

print(continents)

# for continent in continents:
#     print(continent)
    # os.makedirs(f"./data/{continent}", exist_ok=True)
    # for country in countries[]:
    # print(countries[countries['Continent'] == continent])

