#!/usr/bin/env python3
import os
import requests
import numpy as np
import geopandas as gpd

# 1) Rutas
GRID_PATH   = "./data/processed/h3_grid_haiti_res5.geojson"
OUTPUT_PATH = "./data/processed/h3_meteorological_forecast.geojson"

# 2) URL del pronóstico determinista
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# 3) Error mínimo por variable si no hay suficiente variabilidad
MIN_ERROR = {
    "precipitation": 0.20,   # 20%
    "wind_speed_10m": 0.15,  # 15%
    "temperature_2m": 0.05   # 5%
}

def fetch_forecast(lat, lon):
    """Obtiene datos horarios de precipitación, viento y temperatura por 7 días."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "precipitation,wind_speed_10m,temperature_2m",
        "forecast_days": 7
    }
    r = requests.get(FORECAST_URL, params=params, timeout=10)
    r.raise_for_status()
    return r.json()["hourly"]

def main(grid_path, output_path):
    # Leer la grilla H3
    gdf = gpd.read_file(grid_path).to_crs("EPSG:4326")

    # Inicializar columnas de salida
    fields = [
        "Best Case: Precipitation", "Likely: Precipitation", "Worst Case: Precipitation",
        "Best Case: Wind Speed", "Likely: Wind Speed", "Worst Case: Wind Speed",
        "Best Case: Temperature", "Likely: Temperature", "Worst Case: Temperature"
    ]
    for field in fields:
        gdf[field] = np.nan

    # Procesar cada hexágono
    for idx, row in gdf.iterrows():
        lat, lon = row.geometry.centroid.y, row.geometry.centroid.x
        try:
            data = fetch_forecast(lat, lon)

            # Precipitación acumulada
            precip = np.array(data["precipitation"])
            prec_sum = precip.sum()
            std_precip = max(precip.std(), prec_sum * MIN_ERROR["precipitation"])
            gdf.at[idx, "Best Case: Precipitation"] = max(prec_sum - std_precip, 0)
            gdf.at[idx, "Likely: Precipitation"] = prec_sum
            gdf.at[idx, "Worst Case: Precipitation"] = prec_sum + std_precip

            # Viento máximo
            wind = np.array(data["wind_speed_10m"])
            wmax = wind.max()
            std_wind = max(wind.std(), wmax * MIN_ERROR["wind_speed_10m"])
            gdf.at[idx, "Best Case: Wind Speed"] = max(wmax - std_wind, 0)
            gdf.at[idx, "Likely: Wind Speed"] = wmax
            gdf.at[idx, "Worst Case: Wind Speed"] = wmax + std_wind

            # Temperatura máxima
            temp = np.array(data["temperature_2m"])
            tmax = temp.max()
            std_temp = max(temp.std(), tmax * MIN_ERROR["temperature_2m"])
            gdf.at[idx, "Best Case: Temperature"] = max(tmax - std_temp, 0)
            gdf.at[idx, "Likely: Temperature"] = tmax
            gdf.at[idx, "Worst Case: Temperature"] = tmax + std_temp

            print(f"[{idx+1}/{len(gdf)}] h3_id={row.get('h3_id', idx)} procesado")

        except Exception as e:
            print(f"[{idx+1}/{len(gdf)}] Error en h3_id={row.get('h3_id', idx)}: {e}")
            continue

    # Guardar archivo GeoJSON
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    gdf.to_file(output_path, driver="GeoJSON")
    print(f"[✓] Archivo exportado en: {output_path}")

if __name__ == "__main__":
    main()
