#######################
# Import libraries
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import streamlit as st
import geopandas as gpd
import numpy as np
import plotly.express as px
import requests
import pydeck as pdk
import os
from load_countries_continents import continents, df as country_details
from pipeline import starts

#######################
# Page configuration
st.set_page_config(
    page_title="UN Ahead of the Storm",
    page_icon="🌎",
    layout="wide")

alt.themes.enable("dark")

#######################
# CSS styling
st.markdown("""
<style>

[data-testid="block-container"] {
    padding-left: 2rem;
    padding-right: 2rem;
    padding-top: 1rem;
    padding-bottom: 0rem;
    margin-bottom: -7rem;
}

[data-testid="stVerticalBlock"] {
    padding-left: 0rem;
    padding-right: 0rem;
}

[data-testid="stMetric"] {
    background-color: #393939;
    text-align: center;
    padding: 15px 0;
}

[data-testid="stMetricLabel"] {
  display: flex;
  justify-content: center;
  align-items: center;
}

[data-testid="stMetricDeltaIcon-Up"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}

[data-testid="stMetricDeltaIcon-Down"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}

</style>
""", unsafe_allow_html=True)


#######################
# Plots
os.environ['OGR_GEOJSON_MAX_OBJ_SIZE'] = '0'

world_gdf = gpd.read_file("https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json")
world_gdf = world_gdf.to_crs("EPSG:4326")

# ---------- HELPERS & CACHING ---------- #
@st.cache_data(show_spinner=False)
def fetch_country_geojson(continent, iso):
    """
    Download the country outline from world.geo.json.
    Example URL: https://raw.githubusercontent.com/johan/world.geo.json/master/countries/USA.geo.json
    """
    path = os.path.join("data_v2", continent, iso, "boundarie.geojson")
    gdf  = gpd.read_file(path)                                         # :contentReference[oaicite:1]{index=1}
    gdf = gdf.to_crs("EPSG:4326")     # make sure it's in WGS‑84
    gdf = gdf.explode(index_parts=True, ignore_index=True)            # 1 row per polygon
    return gdf

# ---------- MAIN UI ---------- #
continent = st.selectbox("🌐 Select a continent", sorted(continents))
countries  = country_details[country_details['Continent'] == continent].get('boundaryISO')
country_name = st.selectbox("🏳️ Select a country in that continent", countries)

if country_name:
    # flag the selected country
    world_gdf["highlight"] = world_gdf["id"] == country_name

    starts(continent=continent, iso=country_name, resolution=4)


    fig = px.choropleth(

        world_gdf,
        geojson=world_gdf.geometry,
        locations=world_gdf.index,
        color="highlight",
        color_discrete_map={False: "lightgrey", True: "crimson"},
        projection="natural earth",
        hover_name="name",
        width=800,
        height=800,
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin=dict(l=0, r=0, t=50, b=0))

    st.subheader(f"{country_name} highlighted on world map")
    st.plotly_chart(fig)