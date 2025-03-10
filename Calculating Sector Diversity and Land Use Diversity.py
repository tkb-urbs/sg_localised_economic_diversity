# import all libraries needed to do analysis
import pandas as pd
import geopandas as gpd # needed to handle geojson files
import shapely.geometry as geom
from shapely.geometry import Polygon
import statistics
import numpy as np
import re

# import data on companies that I need for analysis and convert to gdf in SVY21
sg_companies = pd.read_csv('sg_all_companies_geocoded.csv')
sg_companies_gdf = gpd.GeoDataFrame(
    sg_companies, geometry=gpd.points_from_xy(sg_companies.Longitude, sg_companies.Latitude), crs="EPSG:4326"
)
sg_companies_svy21 = sg_companies_gdf.to_crs(epsg=3414)
sg_companies_svy21 = sg_companies_svy21.drop(['Latitude', 'Longitude'], axis = 1)

# this set of code sets the boundaries for the grids I want to create
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

# set boundaries of all my grids to these bounds
min_x, min_y, max_x, max_y = masterplan_svy21.total_bounds

# this set of code aims to create grids of differing sizes for analysis

# define a function to create grid with cells of desired size
# it will take cell size as input and output a geodataframe that can be used or exported
def grid_generator(cell_length):
    cell_size = cell_length
    # create a list to append cells to
    grid_cells = []
    x = min_x
    while x < max_x:
        y = min_y
        while y < max_y:
            # Create a grid cell based on desired size
            cell = Polygon([
                (x, y),
                (x + cell_size, y),
                (x + cell_size, y + cell_size),
                (x, y + cell_size),
            ])
            grid_cells.append(cell)
            y += cell_size  # Move in the y direction by the size of the grid cell
        x += cell_size  # Move in the x direction by the size of the grid cell
    # Place grid cells into geodataframe
    grid_gdf = gpd.GeoDataFrame(geometry=grid_cells)
    # Set coordinate system to SVY21
    grid_gdf.set_crs(masterplan_svy21.crs, inplace=True)
    grid_gdf['id'] = range(1, len(grid_gdf) + 1)
    grid_gdf = grid_gdf[['id', 'geometry']]
    return grid_gdf

# define a function that returns the natural log of a number and returns 0 if number is 0 or less
def nat_log(x):
    if x > 0:
        result = np.log(x)
        return result
    else:
        result = 0
        return result

# define functions needed to calculate land use diversity
def lu_diversity_calculator(cell_number):
    # create data frame will all land use data about the cell
    cell_LU = LU_grid[LU_grid['id'] == cell_number]
    
    # Find the total land area of the cell
    cell_area = sum(cell_LU['area'])
    # Find area taken up by each land use
    LU_freq = cell_LU.groupby(['lu_desc'])['area'].sum().reset_index(name='area')
    LU_freq['p'] = LU_freq['area']/cell_area
    
    # Calculate shannon-weaver diversity index step-by-step
    # Start with natural log of p
    LU_freq['ln p'] = LU_freq['p'].apply(nat_log)
    LU_freq['product'] = LU_freq['p']*LU_freq['ln p']
    # return diversity index
    H = -(sum(LU_freq['product']))
    return H

def lu_equitability_calculator(index, cell_number):
    cell_LU = LU_grid[LU_grid['id'] == cell_number]
    S = len(cell_LU['lu_desc'].unique())
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
def sector_diversity_calculator(cell_number):
    cell_companies = company_grid[company_grid['id'] == cell_number]
    #cell_companies['primary_ssic_code_str'] = cell_companies['primary_ssic_code'].apply(str)
    
    # Create a frequency table and convert to fraction of all companies
    cell_freq = cell_companies.groupby(['primary_ssic_code'])['entity_name'].count().reset_index(name='Count')
    total_companies = sum(cell_freq['Count'])
    cell_freq['p'] = cell_freq['Count']/total_companies
    
    # Create derivatives for Shannon-Weaver Index
    cell_freq['ln p'] = cell_freq['p'].apply(nat_log)
    cell_freq['product'] = cell_freq['p']*cell_freq['ln p']

    H = -sum(cell_freq['product'])

    return H

def sector_equitability_calculator(index, cell_number):
    cell_df = company_grid[company_grid['id'] == cell_number]
    S = len(cell_df['primary_ssic_code'].unique())
    if S > 0:
        lnS = np.log(S)
        if lnS == 0:
            E = 1
        else:
            E = index/lnS
    else:
        E = 1
    return E

# create a list of cell sizes
cell_sizes = []
for i in range(200, 2050, 50):
    cell_sizes.append(i)

# create lists for other summary statistics
sector_H_means = []
sector_E_means = []
LU_H_means = []
LU_E_means = []

sector_H_sds = []
sector_E_sds = []
LU_H_sds = []
LU_E_sds = []

for size in cell_sizes:
    # generate grid of desired size
    grid_gdf = grid_generator(size)
    
    # set up gdf for land use diversity analysis
    LU_grid = gpd.overlay(grid_gdf, masterplan_svy21, how='intersection')
    LU_grid['area'] = LU_grid.geometry.area
    
    # create list of cell id to run through and empty lists for data on each cell
    LU_cell_ids = list(LU_grid['id'].unique())
    LU_diversity = []
    LU_equitability = []

    # create loop to run through different cells and caluclate LU diversity
    for cell in LU_cell_ids:
        # calculate land use diversity 
        LU_H = lu_diversity_calculator(cell)
        LU_diversity.append(LU_H)
        
        # calculate land use equitability
        LU_E = lu_equitability_calculator(LU_H, cell)
        LU_equitability.append(LU_E)
    
    # put land use diversity data in data frame
    dict = {'id':LU_cell_ids,
       'LU diversity':LU_diversity,
       'LU equitability':LU_equitability}

    LU_data = pd.DataFrame(dict)

    # collect summary statistics about the land use diversity of cells
    LU_H_mean = statistics.mean(LU_diversity)
    LU_H_means.append(LU_H_mean)
    LU_E_mean = statistics.mean(LU_equitability)
    LU_E_means.append(LU_E_mean)
    
    LU_H_sd = statistics.stdev(LU_diversity)
    LU_H_sds.append(LU_H_sd)
    LU_E_sd = statistics.stdev(LU_equitability)
    LU_E_sds.append(LU_E_sd)
    
    
    # set up gdf for sector diversity analysis
    company_grid = gpd.overlay(grid_gdf, sg_companies_svy21, how ='intersection', keep_geom_type=False)
    company_grid = company_grid.drop(['geometry'], axis = 1)
    company_grid = company_grid.merge(grid_gdf, how = 'left', on = 'id')
    
    # create list of cell id to run through
    cell_ids = list(company_grid['id'].unique())
    sect_diversity = []
    sect_equitability = []

    # create loop to run through different cells and calculate sector diversity
    for cell in cell_ids:
        # calculate sector diversity
        H = sector_diversity_calculator(cell)
        sect_diversity.append(H)
        
        # calculate sector equitability
        E = sector_equitability_calculator(H, cell)
        sect_equitability.append(E)
    
    # put sector diversity data in data frame
    dict = {'id':cell_ids,
       'sect diversity':sect_diversity,
       'sect equitability':sect_equitability}

    sector_data = pd.DataFrame(dict)

    # collect summaries of sector statistics
    sector_H_mean = statistics.mean(sect_diversity)
    sector_H_means.append(sector_H_mean)
    sector_E_mean = statistics.mean(sect_equitability)
    sector_E_means.append(sector_E_mean)
    
    sector_H_sd = statistics.stdev(sect_diversity)
    sector_H_sds.append(sector_H_sd)
    sector_E_sd = statistics.stdev(sect_equitability)
    sector_E_sds.append(sector_E_sd)

    # merge sector data and land use data together and export
    diversity_data = sector_data.merge(LU_data, how = 'left', on = 'id')
    diversity_gdf = grid_gdf.merge(diversity_data, how = 'left', on = 'id')
    diversity_gdf.to_file(str(size) + '_sect_LU_diversity.geojson', driver = 'GeoJSON')

# combine summary statistics for each grid size
dict = {'cell size':cell_sizes,
       'LU_H_means':LU_H_means,
       'LU_E_means':LU_E_means,
        'LU_H_sds': LU_H_sds,
        'LU_E_sds': LU_E_sds,
        'sector_H_means': sector_H_means,
        'sector_E_means': sector_E_means,
        'sector_H_sds': sector_H_sds,
        'sector_E_sds': sector_E_sds
       }

grid_size_data = pd.DataFrame(dict)
grid_size_data.to_csv('test_grid_size_effect.csv')
