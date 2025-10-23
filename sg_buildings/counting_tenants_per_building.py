# -*- coding: utf-8 -*-
"""
Created on Thu Oct 23 12:09:05 2025

@author: tkbean
"""

# import all libraries needed to do analysis
import pandas as pd
import geopandas as gpd # needed to handle geojson files

# import building data from OSM
buildings = gpd.read_file(r"sg_buildings.geojson")

# ensure file is in SVY21 coordinates system
buildings_selcols = buildings[["id", "geometry"]]
buildings_svy21 = buildings_selcols.to_crs(epsg=3414)
buildings_svy21['footprint'] = buildings_svy21.area # find area of each building

# import data on companies that I need for analysis and convert to gdf in SVY21
sg_companies = pd.read_csv(r"sg_all_companies_geocoded.csv")
sg_companies_gdf = gpd.GeoDataFrame(sg_companies, geometry=gpd.points_from_xy(sg_companies.Longitude, sg_companies.Latitude), crs="EPSG:4326")
sg_companies_svy21 = sg_companies_gdf.to_crs(epsg=3414)
sg_companies_svy21 = sg_companies_svy21.drop(['Latitude', 'Longitude'], axis = 1)

# Intersect the cadastral lots with the company dataset
building_companies = gpd.overlay(buildings_svy21, sg_companies_svy21, how ='intersection', keep_geom_type=False)
building_companies = building_companies.drop(['geometry'], axis = 1)

# Calculate diversity for each land use and export csv
# Create list of unqiue land uses
bdg_list = list(building_companies['id'].unique())
tenant_count = []

for bdg in bdg_list:
    
    tenants = building_companies[building_companies['id'] == bdg]
    tenant_count.append(tenants.shape[0])
        
# put sector diversity data in data frame
dict = {'building_id':bdg_list,
       'tenant_total':tenant_count}

building_data = pd.DataFrame(dict)

# add back lot coordinates for spatial visualisation
buildings_svy21 = buildings_svy21.rename(columns = {"id":"building_id"})
geo_bdg_data = pd.merge(building_data, buildings_svy21, how='left', on='building_id')
gdf_bdg_data = gpd.GeoDataFrame(geo_bdg_data, geometry='geometry', crs = "EPSG:3414")

# export data as geojson
gdf_bdg_data.to_file(r"building_tenant_counts.geojson", driver = 'GeoJSON')
