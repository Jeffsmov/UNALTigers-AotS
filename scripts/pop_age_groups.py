#!/usr/bin/env python3
import os
import geopandas as gpd
import pandas as pd
import numpy as np
from rasterstats import zonal_stats

def load_wpp_props(xlsx_path, year = '2020', iso3 = "HTI") -> dict:
    """
    Lee la hoja 'Estimates' del WPP y devuelve las proporciones de población
    infantil para <5, <10 y <15 años.
    """
    df = pd.read_excel(
        xlsx_path,
        sheet_name="Estimates",
        header=0
    )
    df2020 = df[(df["Year"] == year) & (df["ISO3 Alpha-code"] == iso3)]
    if df2020.empty:
        raise ValueError(f"No se encontraron datos para {iso3} en {year}")
    row = df2020.iloc[0]

    age_cols = [c for c in df.columns if "-" in c and c.split("-")[0].isdigit()]
    total = row[age_cols].sum()

    return {
        "p_u5":  row["0 a 4"] / total,
        "p_u10": (row["0 a 4"] + row["5 a 9"]) / total,
        "p_u15": (row["0 a 4"] + row["5 a 9"] + row["10 a 14"]) / total
    }

def sample_pop(grid: gpd.GeoDataFrame, raster_path: str, field: str) -> None:
    """
    Muestrea suma de población total desde un raster WorldPop en cada hexágono.
    Añade columna `field` al GeoDataFrame.
    """
    stats = zonal_stats(
        vectors=grid.geometry,
        raster=raster_path,
        stats=["sum"],
        nodata=None,
        all_touched=True
    )
    grid[field] = [s["sum"] or 0 for s in stats]

def standardize_child_population(
    h3_input_path: str,
    wpp_xlsx: str,
    raster_path: str,
    h3_output_path: str,
    year: int = 2020,
    iso3: str = "HTI"
) -> None:
    """
    Ejecuta todo el flujo:
      1. Carga proporciones WPP
      2. Carga grilla H3
      3. Muestrea población total
      4. Calcula pop_u5, pop_u10, pop_u15
      5. Calcula densidades (<5, <10, <15) en habitantes/km²
      6. Normaliza (min-max) cada densidad
      7. Renombra columnas a nombres amigables
      8. Guarda solo columnas normalizadas + geometría
    """
    # 1. Leer proporciones WPP
    props = load_wpp_props(wpp_xlsx, year, iso3)

    # 2. Cargar grilla H3
    h3 = gpd.read_file(h3_input_path)

    # 3. Muestrear población total
    sample_pop(h3, raster_path, "pop_total")

    # 4. Calcular población infantil por hexágono
    h3["pop_u5"]  = h3["pop_total"] * props["p_u5"]
    h3["pop_u10"] = h3["pop_total"] * props["p_u10"]
    h3["pop_u15"] = h3["pop_total"] * props["p_u15"]

    # 5. Calcular densidades (hab/km²)
    #    Proyectar a métrica para área precisa
    orig_crs = h3.crs
    h3 = h3.to_crs(epsg=3857)
    h3["area_km2"] = h3.geometry.area / 1e6
    h3["densidad_u5"]  = h3["pop_u5"]  / h3["area_km2"]
    h3["densidad_u10"] = h3["pop_u10"] / h3["area_km2"]
    h3["densidad_u15"] = h3["pop_u15"] / h3["area_km2"]

    # 6. Normalización Min-Max
    for col in ["densidad_u5", "densidad_u10", "densidad_u15"]:
        min_val = h3[col].min()
        max_val = h3[col].max()
        h3[f"{col}_norm"] = (h3[col] - min_val) / (max_val - min_val)

    # 7. Renombrar columnas para el usuario
    rename_map = {
        "densidad_u5_norm":  "Densidad <5 años (normalizada)",
        "densidad_u10_norm": "Densidad <10 años (normalizada)",
        "densidad_u15_norm": "Densidad <15 años (normalizada)"
    }
    h3 = h3.rename(columns=rename_map)

    # 8. Seleccionar solo las tres columnas normalizadas y geometría
    result = h3[
        ["Densidad <5 años (normalizada)",
         "Densidad <10 años (normalizada)",
         "Densidad <15 años (normalizada)",
         "geometry"]
    ].copy()

    # Volver al CRS original y guardar
    result = result.to_crs(orig_crs)
    os.makedirs(os.path.dirname(h3_output_path), exist_ok=True)
    result.to_file(h3_output_path, driver="GeoJSON")
    print(f"[✓] Indicadores normalizados guardados en: {h3_output_path}")

if __name__ == "__main__":
    standardize_child_population(
        h3_input_path="./data/processed/h3_grid_haiti_res7.geojson",
        wpp_xlsx="./data/raw/worldpop/WPP2024_POP_F02_1_POPULATION_5-YEAR_AGE_GROUPS_BOTH_SEXES.xlsx",
        raster_path="./data/raw/worldpop/ppp_2020_1km_Aggregated.tif",
        h3_output_path="./data/processed/h3_age_haiti_standardized.geojson",
        year=2020,
        iso3="HTI"
    )
