# -*- coding: utf-8 -*-
"""
Created on Tue Nov 11 12:18:47 2025

@author: tkbean
"""

# import all libraries needed to do analysis
import pandas as pd
import geopandas as gpd # needed to handle geojson files
import statistics as st
from bs4 import BeautifulSoup

# import building data from OSM
buildings = gpd.read_file(r"sg_buildings.geojson")

# ensure file is in SVY21 coordinates system
buildings_selcols = buildings[["id", "geometry"]]
buildings_svy21 = buildings_selcols.to_crs(epsg=3414)
buildings_svy21['footprint'] = buildings_svy21.area # find area of each lot

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
masterplan = gpd.read_file(r"MasterPlan2019LandUselayer.geojson")

# ensure file is in SVY21 coordinates system
masterplan_svy21 = masterplan.to_crs(epsg=3414)
masterplan_svy21 = data_editor(masterplan_svy21) #parse description data into separate tables

# intersect buildings with masterplan to include masterplan information in buildings
building_mp = gpd.overlay(buildings_svy21, masterplan_svy21, how ='intersection', keep_geom_type=False)
building_mp = building_mp.drop(['geometry'], axis = 1)

# work through each building to assign a single value. 
# If all data are strings, assign GPR "not specified". 
# If there are some numerical data, remove non-numerical data and assign mean as GPR
def GPR_estimator(bdg):
    bdg_info = building_mp[building_mp['id'] == bdg]
    
    if bdg_info.shape[0] < 1:
        return 'NA'
    else:
        return st.mode(bdg_info['GPR'])

def LU_estimator(bdg):
    bdg_info = building_mp[building_mp['id'] == bdg]
    
    if bdg_info.shape[0] < 1:
        return 'NA'
    
    elif st.mode(bdg_info['LU_DESC']) == 'ROAD':
        new_bdg_info = bdg_info[bdg_info['LU_DESC'] != 'ROAD']
        
        if new_bdg_info.shape[0] < 1:
            return 'NA'
        
        else: 
            return st.mode(new_bdg_info['LU_DESC'])
     
    else:
        return st.mode(bdg_info['LU_DESC'])

bdg_list= list(buildings['id'].unique())
est_GPR = []
est_LU = []

for b in bdg_list:
    new_GPR = GPR_estimator(b)
    est_GPR.append(new_GPR)
    
    new_LU = LU_estimator(b)
    est_LU.append(new_LU)
    
# put estimated building data from masterplan in data frame
dict = {'building_id':bdg_list,
       'est_GPR':est_GPR,
       'est_LU':est_LU}

mp_data = pd.DataFrame(dict)

# add back building coordinates for spatial visualisation
buildings_svy21 = buildings_svy21.rename(columns = {"id":"building_id"})
geo_bdg_data = pd.merge(mp_data, buildings_svy21, how='left', on='building_id')

# export data as geojson
geo_bdg_data.to_csv(r"building_LU_GPR_data.csv")
