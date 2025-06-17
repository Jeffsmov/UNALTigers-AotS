import os

directory = "./data/continents"

LAYER_FILES_file_names = {
    "Population": "h3_age_standardized",
    "Natural Hazards": "h3_hazard_risks",
    "Infrastructure": "h3_infra_indicators_user_friendly",
    "Child Vulnerability": "h3_vulnerability_child",
    "Weather Scenarios": "h3_meteorological_forecast"
}

def load_layer_files():
    result = {}
    
    continentDirectories = next(os.walk(directory))[1]
    
    for continent in continentDirectories:
        countriesDirectory = next(os.walk(directory+"/"+continent))[1]
        for country in countriesDirectory:
            result[country]={
                "Population": f"{directory}/{continent}/{country}/{LAYER_FILES_file_names['Population']}.geojson",
                "Natural Hazards": f"{directory}/{continent}/{country}/{LAYER_FILES_file_names['Natural Hazards']}.geojson",
                "Infrastructure": f"{directory}/{continent}/{country}/{LAYER_FILES_file_names['Infrastructure']}.geojson",
                "Child Vulnerability": f"{directory}/{continent}/{country}/{LAYER_FILES_file_names['Child Vulnerability']}.geojson",
                "Weather Scenarios": f"{directory}/{continent}/{country}/{LAYER_FILES_file_names['Weather Scenarios']}.geojson"
            }
            
    
    return result
