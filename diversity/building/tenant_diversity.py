# -*- coding: utf-8 -*-
"""
Created on Tue Sep 16 15:39:07 2025

@author: tkbean
"""

# import all libraries needed to do analysis
import pandas as pd
import geopandas as gpd # needed to handle geojson files
import numpy as np
import statistics as st
from bs4 import BeautifulSoup

# import building data from OSM
buildings = gpd.read_file(r"sg_buildings.geojson")

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
masterplan = gpd.read_file(r"MasterPlan2019LandUselayer.geojson")

# ensure file is in SVY21 coordinates system
masterplan_svy21 = masterplan.to_crs(epsg=3414)
masterplan_svy21 = data_editor(masterplan_svy21) #parse description data into separate tables

# import data on companies that I need for analysis and convert to gdf in SVY21
sg_companies = pd.read_csv(r"sg_all_companies_geocoded.csv")
sg_companies_gdf = gpd.GeoDataFrame(sg_companies, geometry=gpd.points_from_xy(sg_companies.Longitude, sg_companies.Latitude), crs="EPSG:4326")
sg_companies_svy21 = sg_companies_gdf.to_crs(epsg=3414)
sg_companies_svy21 = sg_companies_svy21.drop(['Latitude', 'Longitude'], axis = 1)

# Intersect the cadastral lots with the company dataset
building_companies = gpd.overlay(buildings_svy21, sg_companies_svy21, how ='intersection', keep_geom_type=False)
building_companies = building_companies.drop(['geometry'], axis = 1)

# define functions to calculate diversity
# define a function that returns the natural log of a number and returns 0 if number is 0 or less
def nat_log(x):
    if x > 0:
        result = np.log(x)
        return result
    else:
        result = 0
        return result

# calculate sector diversity
def sector_diversity_calculator(bdg):
    tenants = building_companies[building_companies['id'] == bdg]
    
    # Create a frequency table and convert to fraction of all companies
    tnt_freq = tenants.groupby(['primary_ssic_code'])['entity_name'].count().reset_index(name='Count')
    total_companies = sum(tnt_freq['Count'])
    tnt_freq['p'] = tnt_freq['Count']/total_companies
    
    # Create derivatives for Shannon-Weaver Index
    tnt_freq['ln p'] = tnt_freq['p'].apply(nat_log)
    tnt_freq['product'] = tnt_freq['p']*tnt_freq['ln p']

    H = -sum(tnt_freq['product'])

    return H

def sector_equitability_calculator(d_index, bdg):
    bdg_df = building_companies[building_companies['id'] == bdg]
    S = len(bdg_df['primary_ssic_code'].unique())
    if S > 0:
        lnS = np.log(S)
        if lnS == 0:
            E = 1
        else:
            E = d_index/lnS
    else:
        E = 1
    return E

# Calculate diversity for each land use and export csv
# Create list of unqiue land uses
bdg_list= list(building_companies['id'].unique())
sect_diversity = []
sect_equitability = []

for bdg in bdg_list:
    # calculate sector diversity
        H = sector_diversity_calculator(bdg)
        sect_diversity.append(H)
        
        # calculate sector equitability
        E = sector_equitability_calculator(H, bdg)
        sect_equitability.append(E)
        
# put sector diversity data in data frame
dict = {'building_id':bdg_list,
       'sect diversity':sect_diversity,
       'sect equitability':sect_equitability}

building_data = pd.DataFrame(dict)

# merge building geometry to building id and export this data first

# intersect buildings with masterplan to include masterplan information in cadastral lots
building_mp = gpd.overlay(buildings_svy21, masterplan_svy21, how ='intersection', keep_geom_type=False)
building_mp = building_mp.drop(['geometry'], axis = 1)

# work through each lot to assign a single value. 
# If all data are strings, assign GPR "not specified". 
# If there are some numerical data, remove non-numerical data and assign mean as GPR
def GPR_estimator(bdg):
    bdg_info = building_mp[building_mp['id'] == bdg]
    return st.mode(bdg_info['GPR'])

def LU_estimator(bdg):
    bdg_info = building_mp[building_mp['id'] == bdg]
    return st.mode(bdg_info['LU_DESC'])

bdg_list= list(building_companies['id'].unique())
est_GPR = []
est_LU = []

for b in bdg_list:
    new_GPR = GPR_estimator(b)
    est_GPR.append(new_GPR)
    
    new_LU = LU_estimator(b)
    est_LU.append(new_LU)
    
# put estimated lot data from masterplan in data frame
dict = {'building_id':bdg_list,
       'est_GPR':est_GPR,
       'est_LU':est_LU}

mp_data = pd.DataFrame(dict)

# merge all data on each lot together
full_bdg_data = pd.merge(building_data, mp_data, how='left', on='building_id')

# add back lot coordinates for spatial visualisation
buildings_svy21 = buildings_svy21.rename(columns = {"id":"building_id"})
geo_bdg_data = pd.merge(full_bdg_data, buildings_svy21, how='left', on='building_id')

# export data as geojson
geo_bdg_data.to_csv("building_diversity_data.csv")
