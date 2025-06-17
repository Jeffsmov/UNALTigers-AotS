#!/usr/bin/env python3
import os
import geopandas as gpd
import h3
from shapely.geometry import Polygon, mapping

def generate_h3_grid_from_boundary(boundary_geojson: str, resolution: int):
    # 1) Carga y unifica tu límite en EPSG:4326
    b = gpd.read_file(boundary_geojson).to_crs("EPSG:4326")
    poly = b.geometry.unary_union

    # 2) Obtiene todos los índices H3 de la resolución dada
    #    geo_to_cells espera un objeto __geo_interface__ (GeoJSON-like) :contentReference[oaicite:0]{index=0}
    cells = h3.geo_to_cells(mapping(poly), resolution)

    # 3) Convierte cada índice en un Polígono (lng,lat) :contentReference[oaicite:1]{index=1}
    records = []
    for cell in cells:
        boundary = h3.cell_to_boundary(cell)  # devuelve lista de (lat,lng) :contentReference[oaicite:2]{index=2}
        geom = Polygon([(lng, lat) for lat, lng in boundary])
        records.append({"h3_id": cell, "geometry": geom})

    return gpd.GeoDataFrame(records, crs="EPSG:4326")

def main():
    boundary_path = "./data/raw/boundries/geoBoundaries-HTI-ADM3_simplified.geojson" # ARCHIVO RUBEN
    out_dir       = "./data/processed" # OUTPUT DIR
    resolution    = 6  # Cambia a 7, 8, 12 para ver hexágonos de distinto tamaño

    os.makedirs(out_dir, exist_ok=True)

    grid = generate_h3_grid_from_boundary(boundary_path, resolution)
    out_path = os.path.join(out_dir, f"h3_grid_haiti_res{resolution}.geojson")
    grid.to_file(out_path, driver="GeoJSON")
    print(f"[✓] Generado h3_grid_haiti_res{resolution}.geojson con {len(grid)} celdas")

if __name__ == "__main__":
    main()
