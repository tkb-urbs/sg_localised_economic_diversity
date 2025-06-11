# -*- coding: utf-8 -*-
"""
Created on Wed Jun 11 19:41:33 2025

@author: tkbean
"""

# import all libraries needed to do analysis
import pandas as pd
import geopandas as gpd # needed to handle geojson files
import shapely.geometry as geom
from shapely.geometry import Polygon
import re

# file is URA 2019 Masterplan published by URA
masterplan = gpd.read_file(r"C:\Users\tkbean\Documents\2 Research\5 Ubi Project\0a Python Analysis of QGIS Grid\MasterPlan2019LandUselayer.geojson")

# ensure file is in SVY21 coordinates system
masterplan_svy21 = masterplan.to_crs(epsg=3414)

# Extract land use from description into separate column
def lu_extractor(desc):
    lu_desc = re.findall('<th>LU_DESC<\/th> <td>(.*)</td> </tr><tr bgcolor=""> <th>LU_TEXT</th>', desc)
    lu_desc_cleaned = lu_desc[0]
    return lu_desc_cleaned

masterplan_svy21['lu_desc'] = masterplan_svy21['Description'].apply(lu_extractor)

# import map of subzones and set to SVY21 coordinates
subzone_boundaries = gpd.read_file(r"C:\Users\tkbean\Documents\2 Research\5 Ubi Project\0a Python Analysis of QGIS Grid\MasterPlan2019SubzoneBoundaryNoSeaGEOJSON.geojson")

subzone_SVY21 = subzone_boundaries.to_crs(epsg=3414)

# Extract subzone name from description into separate column
def sz_name_extractor(desc):
    sz_name = re.findall('<th>SUBZONE_N<\/th> <td>(.*)<\/td> <\/tr><tr bgcolor=\"#E3E3F3\"> <th>SUBZONE_C<\/th>', desc)
    sz_name_cleaned = sz_name[0]
    return sz_name_cleaned

subzone_SVY21['subzone_name'] = subzone_SVY21['Description'].apply(sz_name_extractor)

# Create list of unqiue land uses
LU_list= list(masterplan_svy21['lu_desc'].unique())
 
# define functions needed to calculate amount of each land use in a cell
def lu_sz_calculator():
    
    # set up gdf for land use diversity analysis
    LU_subzone = gpd.overlay(subzone_SVY21, masterplan_svy21, how='intersection')
    LU_subzone['area'] = LU_subzone.geometry.area # calculates area of polygons after intersection
    
    # create list of subzone names to run through and empty lists for data on each subzone
    sz_names = list(LU_subzone['subzone_name'].unique())
    
    # initialise lists to store LU data of each cell
    OPEN_SPACE, ROAD, PLACE_OF_WORSHIP, COMMERCIAL, BUSINESS_2, UTILITY, WATERBODY, SPORTS_RECREATION, RESERVE_SITE, SPECIAL_USE, RESIDENTIAL, TRANSPORT_FACILITIES, COMMERCIAL_RESIDENTIAL, CIVIC_COMMUNITY_INSTITUTION, EDUCATIONAL_INSTITUTION, PARK, HEALTH_MEDICAL_CARE, RESIDENTIAL_WITH_COMMERCIAL_AT_1ST_STOREY, BUSINESS_1, MASS_RAPID_TRANSIT, BEACH_AREA, LIGHT_RAPID_TRANSIT, CEMETERY, AGRICULTURE, HOTEL, BUSINESS_PARK, WHITE, PORT_AIRPORT, BUSINESS_2_WHITE, BUSINESS_1_WHITE, RESIDENTIAL_INSTITUTION, COMMERCIAL_INSTITUTION, BUSINESS_PARK_WHITE = ([] for i in range(len(LU_list)))
    LU_columns = [OPEN_SPACE, ROAD, PLACE_OF_WORSHIP, COMMERCIAL, BUSINESS_2, UTILITY, WATERBODY, SPORTS_RECREATION, RESERVE_SITE, SPECIAL_USE, RESIDENTIAL, TRANSPORT_FACILITIES, COMMERCIAL_RESIDENTIAL, CIVIC_COMMUNITY_INSTITUTION, EDUCATIONAL_INSTITUTION, PARK, HEALTH_MEDICAL_CARE, RESIDENTIAL_WITH_COMMERCIAL_AT_1ST_STOREY, BUSINESS_1, MASS_RAPID_TRANSIT, BEACH_AREA, LIGHT_RAPID_TRANSIT, CEMETERY, AGRICULTURE, HOTEL, BUSINESS_PARK, WHITE, PORT_AIRPORT, BUSINESS_2_WHITE, BUSINESS_1_WHITE, RESIDENTIAL_INSTITUTION, COMMERCIAL_INSTITUTION, BUSINESS_PARK_WHITE]
    
    # finalise lists and column names used in output data frame
    df_lists = [sz_names] + LU_columns
    column_names = ['subzone_N'] + LU_list
    
    # iterate through each cell and each land use type to calculate LU in each cell
    for sz in sz_names:
        LU_counter = 0 # this number enables us to pull out appropriate list
        sz_LU = LU_subzone[LU_subzone['subzone_name'] == sz]
        sz_area = sum(sz_LU['area'])
        
        # iterate through each land use
        for LU in LU_list:
            # Find area taken up by each land use
            LU_subset = sz_LU[sz_LU['lu_desc'] == LU]
            LU_area = sum(LU_subset['area'])
            
            if LU_area == 0:
                LU_columns[LU_counter].append(0)
                LU_counter += 1
            else:
                LU_percentage = LU_area/sz_area
                LU_columns[LU_counter].append(LU_percentage)
                LU_counter += 1
                
    LU_data = pd.DataFrame(list(zip(*df_lists)), columns=column_names)
    LU_data.to_csv('sz_LU_breakdown.csv')
    
def avg_lot_calculator():
    # set up gdf for land use diversity analysis
    LU_subzone = gpd.overlay(subzone_SVY21, masterplan_svy21, how='intersection')
    LU_subzone['area'] = LU_subzone.geometry.area # calculates area of polygons after intersection
    
    # create list of subzone names to run through and empty lists for data on each subzone
    sz_names = list(LU_subzone['subzone_name'].unique())
    
    # initialise lists to store LU data of each cell
    OPEN_SPACE, ROAD, PLACE_OF_WORSHIP, COMMERCIAL, BUSINESS_2, UTILITY, WATERBODY, SPORTS_RECREATION, RESERVE_SITE, SPECIAL_USE, RESIDENTIAL, TRANSPORT_FACILITIES, COMMERCIAL_RESIDENTIAL, CIVIC_COMMUNITY_INSTITUTION, EDUCATIONAL_INSTITUTION, PARK, HEALTH_MEDICAL_CARE, RESIDENTIAL_WITH_COMMERCIAL_AT_1ST_STOREY, BUSINESS_1, MASS_RAPID_TRANSIT, BEACH_AREA, LIGHT_RAPID_TRANSIT, CEMETERY, AGRICULTURE, HOTEL, BUSINESS_PARK, WHITE, PORT_AIRPORT, BUSINESS_2_WHITE, BUSINESS_1_WHITE, RESIDENTIAL_INSTITUTION, COMMERCIAL_INSTITUTION, BUSINESS_PARK_WHITE = ([] for i in range(len(LU_list)))
    LU_columns = [OPEN_SPACE, ROAD, PLACE_OF_WORSHIP, COMMERCIAL, BUSINESS_2, UTILITY, WATERBODY, SPORTS_RECREATION, RESERVE_SITE, SPECIAL_USE, RESIDENTIAL, TRANSPORT_FACILITIES, COMMERCIAL_RESIDENTIAL, CIVIC_COMMUNITY_INSTITUTION, EDUCATIONAL_INSTITUTION, PARK, HEALTH_MEDICAL_CARE, RESIDENTIAL_WITH_COMMERCIAL_AT_1ST_STOREY, BUSINESS_1, MASS_RAPID_TRANSIT, BEACH_AREA, LIGHT_RAPID_TRANSIT, CEMETERY, AGRICULTURE, HOTEL, BUSINESS_PARK, WHITE, PORT_AIRPORT, BUSINESS_2_WHITE, BUSINESS_1_WHITE, RESIDENTIAL_INSTITUTION, COMMERCIAL_INSTITUTION, BUSINESS_PARK_WHITE]
    
    # finalise lists and column names used in output data frame
    df_lists = [sz_names] + LU_columns
    column_names = ['subzone_name'] + LU_list
    
    # iterate through each cell and each land use type to calculate LU in each cell
    for sz in sz_names:
        LU_counter = 0 # this number enables us to pull out appropriate list
        sz_LU = LU_subzone[LU_subzone['subzone_name'] == sz]
        
        # iterate through each land use
        for LU in LU_list:
            # Find area taken up by each land use
            LU_subset = sz_LU[sz_LU['lu_desc'] == LU]
            
            if LU_subset.shape[0] == 0:
                LU_columns[LU_counter].append(0)
                LU_counter += 1
            else:
                lot_size_mean = (sum(LU_subset['area']))/LU_subset.shape[0]
                LU_columns[LU_counter].append(lot_size_mean)
                LU_counter += 1
                
    LU_data = pd.DataFrame(list(zip(*df_lists)), columns=column_names)
    LU_data.to_csv('sz_LU_lot_sizes.csv')

# Run functions
lu_sz_calculator()
avg_lot_calculator()

