"""
Created on Tue Jun 10 20:59:13 2025

@author: tkbean
"""

# import all libraries needed to do analysis
import pandas as pd
import geopandas as gpd # needed to handle geojson files
import shapely.geometry as geom
from shapely.geometry import Polygon
import re

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

# Create list of unqiue land uses
LU_list= list(masterplan_svy21['lu_desc'].unique())

# set boundaries of all my grids to the bounds of the masterplan
min_x, min_y, max_x, max_y = masterplan_svy21.total_bounds

# this set of code aims to create grids with different cell sizes for analysis
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
 
# define functions needed to calculate amount of each land use in a cell
def lu_calculator(cell_size):
    # generate grid of desired size
    grid_gdf = grid_generator(cell_size)
    
    # set up gdf for land use diversity analysis
    LU_grid = gpd.overlay(grid_gdf, masterplan_svy21, how='intersection')
    LU_grid['area'] = LU_grid.geometry.area #calculate area of all polygons in the grid
    
    # create list of cell id to run through and empty lists for data on each cell
    cell_ids = list(LU_grid['id'].unique()) 
    
    # initialise lists to store LU data of each cell
    OPEN_SPACE, ROAD, PLACE_OF_WORSHIP, COMMERCIAL, BUSINESS_2, UTILITY, WATERBODY, SPORTS_RECREATION, RESERVE_SITE, SPECIAL_USE, RESIDENTIAL, TRANSPORT_FACILITIES, COMMERCIAL_RESIDENTIAL, CIVIC_COMMUNITY_INSTITUTION, EDUCATIONAL_INSTITUTION, PARK, HEALTH_MEDICAL_CARE, RESIDENTIAL_WITH_COMMERCIAL_AT_1ST_STOREY, BUSINESS_1, MASS_RAPID_TRANSIT, BEACH_AREA, LIGHT_RAPID_TRANSIT, CEMETERY, AGRICULTURE, HOTEL, BUSINESS_PARK, WHITE, PORT_AIRPORT, BUSINESS_2_WHITE, BUSINESS_1_WHITE, RESIDENTIAL_INSTITUTION, COMMERCIAL_INSTITUTION, BUSINESS_PARK_WHITE = ([] for i in range(len(LU_list)))
    LU_columns = [OPEN_SPACE, ROAD, PLACE_OF_WORSHIP, COMMERCIAL, BUSINESS_2, UTILITY, WATERBODY, SPORTS_RECREATION, RESERVE_SITE, SPECIAL_USE, RESIDENTIAL, TRANSPORT_FACILITIES, COMMERCIAL_RESIDENTIAL, CIVIC_COMMUNITY_INSTITUTION, EDUCATIONAL_INSTITUTION, PARK, HEALTH_MEDICAL_CARE, RESIDENTIAL_WITH_COMMERCIAL_AT_1ST_STOREY, BUSINESS_1, MASS_RAPID_TRANSIT, BEACH_AREA, LIGHT_RAPID_TRANSIT, CEMETERY, AGRICULTURE, HOTEL, BUSINESS_PARK, WHITE, PORT_AIRPORT, BUSINESS_2_WHITE, BUSINESS_1_WHITE, RESIDENTIAL_INSTITUTION, COMMERCIAL_INSTITUTION, BUSINESS_PARK_WHITE]
    
    # finalise lists and column names used in output data frame
    df_lists = [cell_ids] + LU_columns
    column_names = ['id'] + LU_list
    
    # iterate through each cell and each land use type to calculate LU in each cell
    for cell_no in cell_ids:
        LU_counter = 0 # this number enables us to pull out appropriate list
        cell_LU = LU_grid[LU_grid['id'] == cell_no]
        cell_area = sum(cell_LU['area'])
        
        # iterate through each land use
        for LU in LU_list:
            # Find area taken up by each land use
            LU_area = sum(cell_LU['lu_desc'] == LU)
            if LU_area == 0:
                LU_columns[LU_counter].append(0)
                LU_counter += 1
            else:
                LU_percentage = LU_area/cell_area
                LU_columns[LU_counter].append(LU_percentage)
                LU_counter += 1
                
    LU_data = pd.DataFrame(list(zip(*df_lists)), columns=column_names)
    LU_data.to_csv(str(cell_size) + '_cell_LU_breakdown.csv')
    
# Create list of desired cell sizes
cell_sizes = []
for i in range(200, 2050, 50):
    cell_sizes.append(i)

# Iterate through multiple cell sizes
for size in cell_sizes:
    lu_calculator(size)
