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

# Clean ssic column in building_companies
def ssic_cleaner(code):
    new_code = str(code)
    if len(new_code) < 5:
        final_code = '0' + new_code
    else:
        final_code = new_code
    return final_code

building_companies['primary_ssic_str'] = building_companies['primary_ssic_code'].apply(ssic_cleaner)

# Create list of buildings and an empty data frame
bdg_list = list(building_companies['id'].unique())
bdg_tenant_mix = pd.DataFrame()

# loop through each building and count number of tenants from each sector
for bdg in bdg_list:
    #filter out all comapnies in building
   bdg_tenants = building_companies.loc[building_companies['id'] == bdg]
   
   # Create a frequency table and convert to fraction of all companies
   sect_freq = bdg_tenants.groupby(['primary_ssic_str'])['entity_name'].count().reset_index(name='Count')
   total_companies = sum(sect_freq['Count'])
   sect_freq['bdg_total'] = total_companies
   sect_freq['sect_p'] = sect_freq['Count']/total_companies
   sect_freq['bdg_id'] = bdg
   
   # Attach all frequency tables to a data frame
   bdg_tenant_mix = pd.concat([bdg_tenant_mix, sect_freq])

# Export data to keep a copy
bdg_tenant_mix.to_csv(r"building_tenant_mix_by_sector.csv")

# PART 2
# reformat data for future analysis
tenant_mix_raw = pd.read_csv(r"building_tenant_mix_by_sector.csv")

building_counts = tenant_mix_raw.pivot_table('Count', index = 'bdg_id', columns = 'primary_ssic_str')
building_counts = building_counts.fillna(value = 0)
building_counts.to_csv(r"sector_counts_per_building.csv")

building_proportions = tenant_mix_raw.pivot_table('sect_p', index = 'bdg_id', columns = 'primary_ssic_str')
building_proportions = building_proportions.fillna(value = 0)
building_proportions.to_csv(r"sector_proportions_per_building.csv")
