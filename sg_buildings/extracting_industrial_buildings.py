# WARNING: THIS CODE IS INCOMPLETE
# import all libraries needed to do analysis
import pandas as pd
import geopandas as gpd # needed to handle geojson files
import numpy as np
import statistics as st
from bs4 import BeautifulSoup

# Part 1: Identify buildings in JTC buildings
# import building data from OSM
buildings = gpd.read_file("sg_buildings.geojson")

# ensure file is in SVY21 coordinates system
buildings_selcols = buildings[["id", "geometry"]]
buildings_svy21 = buildings_selcols.to_crs(epsg=3414)

# import JTC estate boundaries pbulished by JTC
estate_boundaries = gpd.read_file("JTCEstateNameBoundaryGEOJSON.geojson")
estate_svy21 = estate_boundaries.to_crs(epsg=3414) # ensure file is in SVY21 coordinates system

# Intersect buildings with JTC estate boundaries
estate_buildings = gpd.overlay(estate_svy21, buildings_svy21, how ='intersection', keep_geom_type=False)

# Parse out data on JTC estates
# parse out data from a row in the description column
def parse_html_table(html):
   soup = BeautifulSoup(html, "html.parser")
   data = {}
   for row in soup.find_all("tr"):
       cells = row.find_all(["th", "td"])
       if len(cells) == 2:  # Skip header rows with colspan
           key = cells[0].get_text(strip=True)
           val = cells[1].get_text(strip=True)
           data[key] = val
   return data

def data_editor(df):
    parsed_data = df["Description"].apply(parse_html_table)
    parsed_df = pd.json_normalize(parsed_data)
    result_df = pd.concat([df.drop(columns=["Description"]), parsed_df], axis=1)
    
    return result_df

estate_buildings = data_editor(estate_buildings)
estate_buildings = estate_buildings.drop(columns=["INC_CRC", "FMEL_UPD_D"])
