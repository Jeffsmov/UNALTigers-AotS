import geopandas as gpd
from rasterstats import zonal_stats
import os

def sample_population(grid_path, raster_path, output_path):
    grid = gpd.read_file(grid_path)

    # Zonal stats: sumar valores de población en cada celda
    stats = zonal_stats(
        vectors=grid.geometry,
        raster=raster_path,
        stats=["sum"],
        nodata=None,
        all_touched=True
    )

    # Añadir columna pop_total al GeoDataFrame
    grid["pop_total"] = [s["sum"] or 0 for s in stats]

    # Asegurar carpeta de salida y guardar
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    grid.to_file(output_path, driver="GeoJSON")
    print(f"Población total por celda guardada en: {output_path}")

if __name__ == "__main__":
    GRID_PATH   = "./data/processed/h3_grid_haiti.geojson"
    RASTER_PATH = "./data/raw/worldpop/ppp_2020_1km_Aggregated.tif"
    OUTPUT_PATH = "./data/processed/h3_population_total.geojson"

    sample_population(GRID_PATH, RASTER_PATH, OUTPUT_PATH)