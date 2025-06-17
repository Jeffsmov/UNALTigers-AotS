from scripts.grid_generator import generate_h3_grid_from_boundary
from scripts.hazards import main as hazards
from scripts.pop_age_groups import standardize_child_population
# from scripts.vulnerability_child import main as vulnerability_child
from scripts.infestructura import load_grid_and_points
import os
from pathlib import Path

import os
from pathlib import Path

def file_exists(path: str) -> bool:
    return Path(path).is_file()

def starts(resolution, continent, iso):
    BASE_PATH     = Path("data_v2") / continent / iso
    BOUNDARY_PATH = BASE_PATH / "boundarie.geojson"
    GRID_PATH     = BASE_PATH / f"h3_grid_res{resolution}.geojson"
    HAZARD_PATH   = BASE_PATH / "hazard.geojson"


    DATA_RAW_PATH = Path("./data/raw")
    POPULATION_TIF = DATA_RAW_PATH / "ppp_2020_1km_Aggregated.tif"
    POPULATION_XLSX = DATA_RAW_PATH / "WPP2024_POP_F02_1_POPULATION_5-YEAR_AGE_GROUPS_BOTH_SEXES.xlsx"
    SAMPLE_POP_AGE_PATH = BASE_PATH / f"h3_age_standardized.geojson"

    EDUCATION_PATH = DATA_RAW_PATH / "education.geojson"
    HOSPITALS_PATH = DATA_RAW_PATH / "hospitales.geojson"

    # INFRA_PATH = BASE_PATH / "infra.geojson"


    if not file_exists(str(BOUNDARY_PATH)):
        return

    if not file_exists(str(GRID_PATH)):
        grid = generate_h3_grid_from_boundary(str(BOUNDARY_PATH), resolution)
        grid.to_file(str(GRID_PATH), driver="GeoJSON")

    if not file_exists(str(HAZARD_PATH)):
        hazards(grid_path=str(GRID_PATH), output_path=str(HAZARD_PATH))

    if not file_exists(str(SAMPLE_POP_AGE_PATH)):
        standardize_child_population(str(GRID_PATH), POPULATION_XLSX, POPULATION_TIF, SAMPLE_POP_AGE_PATH, iso3=iso)

    # if not file_exists(str(INFRA_PATH)):

    # vulnerability_child()



# Ejemplo de llamada
if __name__ == "__main__":
    starts(resolution=4,
           continent="Latin America and the Caribbean",
           iso="ARG")
