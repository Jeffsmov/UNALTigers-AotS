from load_layer_files import load_layer_files
import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.features import GeoJsonTooltip
import branca.colormap as cm
import matplotlib.pyplot as plt
import seaborn as sns
from load_countries_continents import continents, df as country_details
from pipeline import starts

# Page config
st.set_page_config(
    page_title="Risk and Climate Exposure in Haiti",
    layout="wide"
)

# Layer paths
LAYER_FILES = load_layer_files()

COLOR_MAPS = {
    "Population": "YlGnBu_09",
    "Natural Hazards": "OrRd_09"
}


@st.cache_data
def load_layer(layer_name: str, country_name: str) -> gpd.GeoDataFrame:
    path = LAYER_FILES[country_name][layer_name]
    gdf = gpd.read_file(path)
    if 'h3_index' not in gdf.columns:
        gdf['h3_index'] = gdf.index.astype(str)
    return gdf


def add_layer_to_map(m, gdf, field, layer_name, color):
    min_val = gdf[field].min()
    max_val = gdf[field].max()
    colormap = cm.linear.__getattribute__(color).scale(min_val, max_val)
    colormap.caption = f"{layer_name} ({field})"
    colormap.add_to(m)

    style_function = lambda feature: {
        'fillColor': colormap(feature['properties'][field]),
        'color': 'black',
        'weight': 0.3,
        'fillOpacity': 0.7
    }

    tooltip = GeoJsonTooltip(
        fields=[field],
        aliases=[f"{layer_name}: "],
        localize=True
    )

    folium.GeoJson(
        gdf,
        name=layer_name,
        style_function=style_function,
        tooltip=tooltip
    ).add_to(m)


def plot_layer_stats(gdf, field, layer_name):
    st.subheader(f"📊 Statistical Summary: {layer_name} - {field}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Minimum", f"{gdf[field].min():.2f}")
    col2.metric("Mean", f"{gdf[field].mean():.2f}")
    col3.metric("Maximum", f"{gdf[field].max():.2f}")

    st.markdown("### Distribution Plot")
    fig, ax = plt.subplots()

    if gdf[field].nunique() < 10:
        sns.countplot(x=gdf[field], ax=ax)
    elif gdf[field].skew() > 1:
        sns.boxplot(x=gdf[field], ax=ax)
    else:
        sns.histplot(gdf[field], kde=True, ax=ax)

    ax.set_title(f"Distribution of {field} in {layer_name}")
    st.pyplot(fig)


def main():
    st.title(f"🌪️ Risk and Climate Exposure Dashboard")

    st.markdown("""
    Explore key indicators such as population density, natural hazards, infrastructure availability,
    child vulnerability, and meteorological forecasts across Haiti. Use the sidebar to control the view.
    """)

    st.sidebar.header("🔍 Layers & Fields")

    continent = st.sidebar.selectbox("🌐 Select a continent", sorted(continents))
    countries = country_details[country_details['Continent'] == continent].get('boundaryISO')
    country_name = st.sidebar.selectbox("🏳️ Select a country in that continent", countries)

    layers = st.sidebar.multiselect(
        "Available Layers:",
        list(COLOR_MAPS.keys()),
        # default=["Weather Scenarios"]
    )

    if country_name is not None:
        starts(continent=continent, iso=country_name, resolution=4)
        field_map = {}
        for layer in layers:
            gdf = load_layer(layer, country_name)
            numeric_cols = [c for c in gdf.columns if c not in ('h3_index', 'geometry')
                            and pd.api.types.is_numeric_dtype(gdf[c])]
            if numeric_cols:
                field_map[layer] = st.sidebar.selectbox(
                    f"Field for '{layer}'", numeric_cols, index=0
                )
            else:
                st.sidebar.warning(f"'{layer}' has no numeric fields.")

        if layers:
            m = folium.Map(location=[19.0, -72.5], zoom_start=7, tiles='cartodbpositron')
            for layer in layers:
                if layer not in field_map:
                    continue
                gdf = load_layer(layer, country_name)
                field = field_map[layer]
                color = COLOR_MAPS.get(layer, "YlOrRd_09")
                add_layer_to_map(m, gdf, field, layer, color)
            st_folium(m, width=1000, height=600)

            # Add chart per selected layer
            for layer in layers:
                if layer in field_map:
                    gdf = load_layer(layer, country_name)
                    field = field_map[layer]
                    plot_layer_stats(gdf, field, layer)
        else:
            st.info("Select at least one layer to display the map.")


if __name__ == "__main__":
    main()