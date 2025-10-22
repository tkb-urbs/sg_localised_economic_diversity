# -*- coding: utf-8 -*-
"""
Created on Wed Oct 22 12:16:18 2025

@author: tkbean
"""

# import all libraries needed to do analysis
import pandas as pd
import geopandas as gpd # needed to handle geojson files
import statistics as st
from bs4 import BeautifulSoup

# import building data from OSM
buildings = gpd.read_file("sg_buildings.geojson")

# ensure file is in SVY21 coordinates system
buildings_selcols = buildings[["id", "geometry"]]
buildings_svy21 = buildings_selcols.to_crs(epsg=3414)
buildings_svy21['footprint'] = buildings_svy21.area # find area of each building

# the masterplan uses html tables to store data within the geojson
# these functions help seperate it out into columns

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

# import URA 2019 Masterplan published by URA
masterplan = gpd.read_file("MasterPlan2019LandUselayer.geojson")

# ensure file is in SVY21 coordinates system
masterplan_svy21 = masterplan.to_crs(epsg=3414)
masterplan_svy21 = data_editor(masterplan_svy21) #parse description data into separate tables

# intersect buildings with masterplan to include masterplan information in cadastral lots
building_mp = gpd.overlay(buildings_svy21, masterplan_svy21, how ='intersection', keep_geom_type=False)
building_mp = building_mp.drop(['geometry'], axis = 1)

# work through each lot to assign a single value. 
# If all data are strings, assign GPR "not specified". 
# If there are some numerical data, remove non-numerical data and assign mean as GPR
def GPR_estimator(bdg_info):
    return st.mode(bdg_info['GPR'])

def LU_estimator(bdg_info):
    return st.mode(bdg_info['LU_DESC'])

bdg_list= list(buildings_svy21['id'].unique())
est_GPR = []
est_LU = []

for bdg in bdg_list:
    bdg_info = building_mp[building_mp['id'] == bdg]
    bdg_info.dropna()
    
    new_GPR = GPR_estimator(bdg_info)
    est_GPR.append(new_GPR)
    
    new_LU = LU_estimator(bdg_info)
    est_LU.append(new_LU)
    
# put estimated lot data from masterplan in data frame
dict = {'building_id':bdg_list,
       'est_GPR':est_GPR,
       'est_LU':est_LU}

mp_data = pd.DataFrame(dict)

# merge all data on each lot together
full_bdg_data = pd.merge(buildings_svy21, mp_data, how='left', on='building_id')

# export data as geojson
full_bdg_data.to_file("building_masterplan_data.geojson", driver = 'GeoJSON')
