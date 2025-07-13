# -*- coding: utf-8 -*-
"""
Created on Sun Jul 13 13:02:04 2025

@author: tkbean
"""

# import all libraries needed to do analysis
import pandas as pd
import geopandas as gpd # needed to handle geojson files
import numpy as np
import shapely.geometry as geom
from shapely.geometry import Polygon
import re

# file is URA 2019 Masterplan published by URA
masterplan = gpd.read_file("MasterPlan2019LandUselayer.geojson")

# ensure file is in SVY21 coordinates system
masterplan_svy21 = masterplan.to_crs(epsg=3414)

# Extract land use from description into separate column
def lu_extractor(desc):
    lu_desc = re.findall('<th>LU_DESC<\/th> <td>(.*)</td> </tr><tr bgcolor=""> <th>LU_TEXT</th>', desc)
    lu_desc_cleaned = lu_desc[0]
    return lu_desc_cleaned

masterplan_svy21['lu_desc'] = masterplan_svy21['Description'].apply(lu_extractor)
masterplan_svy21["geometry"] = masterplan_svy21["geometry"].buffer(0) # fix geometries

# import data on companies that I need for analysis and convert to gdf in SVY21
sg_companies = pd.read_csv("sg_all_companies_geocoded.csv")
sg_companies_gdf = gpd.GeoDataFrame(
    sg_companies, geometry=gpd.points_from_xy(sg_companies.Longitude, sg_companies.Latitude), crs="EPSG:4326"
)
sg_companies_svy21 = sg_companies_gdf.to_crs(epsg=3414)
sg_companies_svy21 = sg_companies_svy21.drop(['Latitude', 'Longitude'], axis = 1)

# Intersect the firm dataset with the land use dataset
company_by_LU = gpd.overlay(masterplan_svy21, sg_companies_svy21, how ='intersection', keep_geom_type=False)
company_by_LU = company_by_LU.drop(['geometry'], axis = 1)

# define functions to deal calculate diversity
# define a function that returns the natural log of a number and returns 0 if number is 0 or less
def nat_log(x):
    if x > 0:
        result = np.log(x)
        return result
    else:
        result = 0
        return result

# calculate sector diversity
def sector_diversity_calculator(LU_name):
    LU_companies = company_by_LU[company_by_LU['lu_desc'] == LU_name]
    
    # Create a frequency table and convert to fraction of all companies
    LU_freq = LU_companies.groupby(['primary_ssic_code'])['entity_name'].count().reset_index(name='Count')
    total_companies = sum(LU_freq['Count'])
    LU_freq['p'] = LU_freq['Count']/total_companies
    
    # Create derivatives for Shannon-Weaver Index
    LU_freq['ln p'] = LU_freq['p'].apply(nat_log)
    LU_freq['product'] = LU_freq['p']*LU_freq['ln p']

    H = -sum(LU_freq['product'])

    return H

def sector_equitability_calculator(d_index, LU_name):
    LU_df = company_by_LU[company_by_LU['lu_desc'] == LU_name]
    S = len(LU_df['primary_ssic_code'].unique())
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
LU_list= list(masterplan_svy21['lu_desc'].unique())
sect_diversity = []
sect_equitability = []

for LU in LU_list:
    H = sector_diversity_calculator(LU)
    sect_diversity.append(H)
        
    # calculate sector equitability
    E = sector_equitability_calculator(H, LU)
    sect_equitability.append(E)
    
# put sector diversity data in data frame
dict = {'LU_name':LU_list,
       'sect diversity':sect_diversity,
       'sect equitability':sect_equitability}

sector_data = pd.DataFrame(dict)

sector_data.to_csv('sector_diversity_by_LU.csv')
