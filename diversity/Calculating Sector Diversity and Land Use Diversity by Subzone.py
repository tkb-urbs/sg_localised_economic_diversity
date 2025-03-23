# import all libraries needed to do analysis
import pandas as pd
import geopandas as gpd # needed to handle geojson files
import shapely.geometry as geom
from shapely.geometry import Polygon
import statistics
import numpy as np
import re

# import map of subzones and set to SVY21 coordinates
subzone_boundaries = gpd.read_file('MasterPlan2019SubzoneBoundaryNoSeaGEOJSON.geojson')

subzone_SVY21 = subzone_boundaries.to_crs(epsg=3414)

# Extract subzone name from description into separate column
def sz_name_extractor(desc):
    sz_name = re.findall('<th>SUBZONE_N<\/th> <td>(.*)<\/td> <\/tr><tr bgcolor=\"#E3E3F3\"> <th>SUBZONE_C<\/th>', desc)
    sz_name_cleaned = sz_name[0]
    return sz_name_cleaned

subzone_SVY21['subzone_name'] = subzone_SVY21['Description'].apply(sz_name_extractor)

# file is URA 2019 Masterplan published by URA
masterplan = gpd.read_file('MasterPlan2019LandUselayer.geojson')

# ensure file is in SVY21 coordinates system
masterplan_svy21 = masterplan.to_crs(epsg=3414)

# Extract land use from description into separate column
def lu_extractor(desc):
    lu_desc = re.findall('<th>LU_DESC<\/th> <td>(.*)</td> </tr><tr bgcolor=""> <th>LU_TEXT</th>', desc)
    lu_desc_cleaned = lu_desc[0]
    return lu_desc_cleaned

masterplan_svy21['lu_desc'] = masterplan_svy21['Description'].apply(lu_extractor)

# import data on companies that I need for analysis and convert to gdf in SVY21
sg_companies = pd.read_csv('sg_all_companies_geocoded.csv')
sg_companies_gdf = gpd.GeoDataFrame(
    sg_companies, geometry=gpd.points_from_xy(sg_companies.Longitude, sg_companies.Latitude), crs="EPSG:4326"
)
sg_companies_svy21 = sg_companies_gdf.to_crs(epsg=3414)
sg_companies_svy21 = sg_companies_svy21.drop(['Latitude', 'Longitude'], axis = 1)

# define a function that returns the natural log of a number and returns 0 if number is 0 or less
def nat_log(x):
    if x > 0:
        result = np.log(x)
        return result
    else:
        result = 0
        return result

# define functions needed to calculate land use diversity
def lu_diversity_calculator(subzone_N):
    # create data frame will all land use data about the subzone
    subzone_LU = LU_subzone[LU_subzone['subzone_name'] == subzone_N]
    
    # Find the total land area of the subzone
    subzone_area = sum(subzone_LU['area'])
    # Find area taken up by each land use
    LU_freq = subzone_LU.groupby(['lu_desc'])['area'].sum().reset_index(name='area')
    LU_freq['p'] = LU_freq['area']/subzone_area
    
    # Calculate shannon-weaver diversity index step-by-step
    # Start with natural log of p
    LU_freq['ln p'] = LU_freq['p'].apply(nat_log)
    LU_freq['product'] = LU_freq['p']*LU_freq['ln p']
    # return diversity index
    H = -(sum(LU_freq['product']))
    return H

def lu_equitability_calculator(index, subzone_N):
    subzone_LU = LU_subzone[LU_subzone['subzone_name'] == subzone_N]
    S = len(subzone_LU['lu_desc'].unique())
    if S > 0:
        lnS = np.log(S)
        if lnS == 0:
            E = 1
        else:
            E = index/lnS
    else:
        E = 1
    return E

# define functions needed to calculate sector diversity
def sector_diversity_calculator(subzone_N):
    subzone_companies = company_by_subzone[company_by_subzone['subzone_name'] == subzone_N]
    
    # Create a frequency table and convert to fraction of all companies
    subzone_freq = subzone_companies.groupby(['primary_ssic_code'])['entity_name'].count().reset_index(name='Count')
    total_companies = sum(subzone_freq['Count'])
    subzone_freq['p'] = subzone_freq['Count']/total_companies
    
    # Create derivatives for Shannon-Weaver Index
    subzone_freq['ln p'] = subzone_freq['p'].apply(nat_log)
    subzone_freq['product'] = subzone_freq['p']*subzone_freq['ln p']

    H = -sum(subzone_freq['product'])

    return H

def sector_equitability_calculator(index, subzone_N):
    subzone_df = company_by_subzone[company_by_subzone['subzone_name'] == subzone_N]
    S = len(subzone_df['primary_ssic_code'].unique())
    if S > 0:
        lnS = np.log(S)
        if lnS == 0:
            E = 1
        else:
            E = index/lnS
    else:
        E = 1
    return E

# set up gdf for land use diversity analysis
LU_subzone = gpd.overlay(subzone_SVY21, masterplan_svy21, how='intersection')
LU_subzone['area'] = LU_subzone.geometry.area # calculates area of polygons after intersection
    
# create list of subzone names to run through and empty lists for data on each subzone
LU_sz_names = list(LU_subzone['subzone_name'].unique())
LU_diversity = []
LU_equitability = []

# create loop to run through different subzones and caluclate LU diversity
for sz in LU_sz_names:
    # calculate land use diversity 
    LU_H = lu_diversity_calculator(sz)
    LU_diversity.append(LU_H)
        
    # calculate land use equitability
    LU_E = lu_equitability_calculator(LU_H, sz)
    LU_equitability.append(LU_E)
    
# put land use diversity data in data frame
dict = {'subzone_name':LU_sz_names,
       'LU diversity':LU_diversity,
       'LU equitability':LU_equitability}

LU_data = pd.DataFrame(dict)
    
# set up gdf for sector diversity analysis
company_by_subzone = gpd.overlay(subzone_SVY21, sg_companies_svy21, how ='intersection', keep_geom_type=False)
company_by_subzone = company_by_subzone.drop(['geometry'], axis = 1)
company_by_subzone = company_by_subzone.merge(subzone_SVY21, how = 'left', on = 'subzone_name')
    
# create list of subzone names to run through
company_sz_names = list(company_by_subzone['subzone_name'].unique())
sect_diversity = []
sect_equitability = []

# create loop to run through different subzones and calculate sector diversity
for sz in company_sz_names:
    # calculate sector diversity
    H = sector_diversity_calculator(sz)
    sect_diversity.append(H)
        
    # calculate sector equitability
    E = sector_equitability_calculator(H, sz)
    sect_equitability.append(E)
    
# put sector diversity data in data frame
dict = {'subzone_name':company_sz_names,
       'sect diversity':sect_diversity,
       'sect equitability':sect_equitability}

sector_data = pd.DataFrame(dict)

# merge sector data and land use data together and export
diversity_data = sector_data.merge(LU_data, how = 'left', on = 'subzone_name')
diversity_gdf = subzone_SVY21.merge(diversity_data, how = 'left', on = 'subzone_name')
diversity_gdf.to_file('subzone_sect_LU_diversity.geojson', driver = 'GeoJSON')
