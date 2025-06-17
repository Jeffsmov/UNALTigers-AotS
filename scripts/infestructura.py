#!/usr/bin/env python3
import os
import geopandas as gpd
import numpy as np
import pandas as pd
from rasterstats import zonal_stats
import osmnx as ox
from shapely.geometry import Polygon
from scipy.spatial import cKDTree

def load_grid_and_points(grid_path, schools_path, hospitals_path):
    """Carga la grilla H3 y la infraestructura en EPSG:4326."""
    grid = (
        gpd.read_file("./data/processed/h3_grid_haiti_res6.geojson").to_crs("EPSG:4326")
    )
    schools   = (
        gpd.read_file("./data/raw/infestructure/educacion.geojson").to_crs("EPSG:4326")
    )
    hospitals = (
        gpd.read_file("./data/raw/infestructure/hospitales.geojson").to_crs("EPSG:4326")
    )
    return grid, schools, hospitals

def download_osm_roads(boundary_geojson):
    """
    Descarga la red vial principal de OSM dentro del límite de Haití.
    """
    b = gpd.read_file(boundary_geojson).to_crs("EPSG:4326")
    poly = b.geometry.unary_union
    G    = ox.graph_from_polygon(
        poly,
        network_type="drive",
        custom_filter='["highway"~"motorway|trunk|primary|secondary"]'
    )
    edges = ox.graph_to_gdfs(G, nodes=False, edges=True)
    return edges.to_crs("EPSG:4326")

def compute_infra_metrics(grid, schools, hospitals, roads):
    """
    Calcula indicadores separados:
      - Número y capacidad de escuelas/hospitales.
      - Densidades por km².
      - Distancia mínima a infraestructura.
      - Longitud y densidad de carreteras.
      - Distancia a la vía principal más cercana.
    """
    grid = grid.copy()

    # 1) Conteo y capacidad
    for df, prefix, label in [
        (schools,   "school",   "escuelas"),
        (hospitals, "hospital", "hospitales")
    ]:
        join = gpd.sjoin(df, grid[["h3_id","geometry"]],
                         how="inner", predicate="within")
        cap_field = "capacity:persons"
        agg = (
            join.groupby("h3_id")
                .agg(
                    count    = ("h3_id",      "size"),
                    capacity = (cap_field,    "sum")
                )
        )
        grid = (
            grid.set_index("h3_id")
                .join(agg)
                .rename(columns={
                    "count":    f"Número de {label}",
                    "capacity": f"Capacidad total de {label}"
                })
                .fillna({
                    f"Número de {label}":           0,
                    f"Capacidad total de {label}":  0
                })
                .reset_index()
        )

    # 2) Área y densidades (hab/km²)
    grid = grid.to_crs(epsg=3857)
    grid["Área (km²)"] = grid.geometry.area / 1e6
    grid["Densidad de escuelas (por km²)"] = grid["Número de escuelas"] / grid["Área (km²)"]
    grid["Densidad de hospitales (por km²)"] = grid["Número de hospitales"] / grid["Área (km²)"]

    # 3) Distancias mínimas a escuela y hospital
    for pts, col, desc in [
        (schools,   "Distancia a escuela más cercana (km)",   "escuela"),
        (hospitals, "Distancia a hospital más cercano (km)", "hospital")
    ]:
        pts_arr   = np.array([[pt.y, pt.x] for pt in pts.geometry])
        tree      = cKDTree(pts_arr)
        centroids = np.array([[pt.y, pt.x]
                              for pt in grid.to_crs(epsg=4326).geometry.centroid])
        d, _      = tree.query(centroids, k=1)
        grid[col] = d * 111.0  # 1° ≈ 111 km

    # 4a) Longitud de carreteras por hexágono
    roads = roads.to_crs(epsg=3857)
    grid  = grid.to_crs(epsg=3857)
    hex_roads = gpd.overlay(
        grid[["h3_id","geometry"]],
        roads[["geometry"]],
        how="intersection"
    )
    hex_roads["Longitud carreteras (km)"] = \
        hex_roads.geometry.length / 1e3
    road_len = (
        hex_roads
        .groupby("h3_id")["Longitud carreteras (km)"]
        .sum()
        .rename("Suma longitud carreteras (km)")
    )
    grid = (
        grid.set_index("h3_id")
            .join(road_len, how="left")
            .fillna({"Suma longitud carreteras (km)": 0})
            .reset_index()
    )
    grid["Densidad vial (km de vía por km²)"] = grid["Suma longitud carreteras (km)"] / grid["Área (km²)"]

    # 4b) Distancia a vía principal más cercana
    road_pts = []
    for line in roads.to_crs(epsg=4326).geometry:
        coords = list(line.coords)[:: max(1, len(line.coords)//10)]
        road_pts.extend(coords)
    pts_arr   = np.array([[lat, lon] for lon, lat in road_pts])
    road_tree = cKDTree(pts_arr)
    centroids = np.array([[pt.y, pt.x]
                          for pt in grid.to_crs(epsg=4326).geometry.centroid])
    d, _      = road_tree.query(centroids, k=1)
    grid["Distancia a vía principal (km)"] = d * 111.0

    # 5) Volver a EPSG:4326 y devolver
    return grid.to_crs(epsg=4326)

if __name__ == "__main__":
    os.makedirs("./data/processed", exist_ok=True)

    grid, schools, hospitals = load_grid_and_points()
    print("[i] Descargando red vial principal de OSM…")
    roads = download_osm_roads(
        "./data/raw/boundries/geoBoundaries-HTI-ADM3_simplified.geojson"
    )

    infra = compute_infra_metrics(grid, schools, hospitals, roads)

    # Exportar solo las columnas user-friendly + geometría
    out_cols = [
        "h3_id",
        "Capacidad total de escuelas",
        "Densidad de escuelas (por km²)",
        "Distancia a escuela más cercana (km)",
        "Densidad de hospitales (por km²)",
        "Distancia a hospital más cercano (km)",
        "Distancia a vía principal (km)",
        "geometry"
    ]
    infra[out_cols].to_file(
        "./data/processed/h3_infra_indicators_user_friendly.geojson",
        driver="GeoJSON"
    )
    print("[✓] Indicadores exportados en h3_infra_indicators_user_friendly.geojson")
