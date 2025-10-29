# Import libraries needed for data processing
import pandas as pd
import geopandas as gpd # needed to handle geojson files
import re

# Import data needed for processing location quotient
sector_national_count = pd.read_csv('all_sector_count.csv')

# SG Companies contains spatial data that needs to be converted from WGS84 to SVY21
sg_companies = pd.read_csv('sg_all_companies_geocoded.csv')
sg_companies_gdf = gpd.GeoDataFrame(
    sg_companies, geometry=gpd.points_from_xy(sg_companies.Longitude, sg_companies.Latitude), crs="EPSG:4326"
)
sg_companies_svy21 = sg_companies_gdf.to_crs(epsg=3414)
sg_companies_svy21 = sg_companies_svy21.drop(['Latitude', 'Longitude'], axis = 1)

# import map of subzones and set to SVY21 coordinates
subzone_boundaries = gpd.read_file('MasterPlan2019SubzoneBoundaryNoSeaGEOJSON.geojson')

subzone_SVY21 = subzone_boundaries.to_crs(epsg=3414)

# Extract subzone name from description into separate column
def sz_name_extractor(desc):
    sz_name = re.findall('<th>SUBZONE_N<\/th> <td>(.*)<\/td> <\/tr><tr bgcolor=\"#E3E3F3\"> <th>SUBZONE_C<\/th>', desc)
    sz_name_cleaned = sz_name[0]
    return sz_name_cleaned

subzone_SVY21['subzone_name'] = subzone_SVY21['Description'].apply(sz_name_extractor)

# Intersect subzone map with companies
company_by_subzone = gpd.overlay(subzone_SVY21, sg_companies_svy21, how ='intersection', keep_geom_type=False)
company_by_subzone = company_by_subzone.drop(['geometry'], axis = 1)
company_by_subzone = company_by_subzone.merge(subzone_SVY21, how = 'left', on = 'subzone_name')

# Clean ssic column in national sector count data
def ssic_cleaner(code):
    new_code = str(code)
    if len(new_code) < 5:
        final_code = '0' + new_code
    else:
        final_code = new_code
    return final_code

sector_national_count['primary_ssic_str'] = sector_national_count['ssic'].apply(ssic_cleaner)

# Find what proportion each sector makes up of all sg companies
total_sg_companies = sum(sector_national_count['live companies'])
sector_national_count['national_p'] = sector_national_count['live companies']/total_sg_companies

all_subzones = list(company_by_subzone['subzone_name'].unique())
subzone_columns = list(company_by_subzone.columns)
sector_distribution_data = pd.DataFrame()

for sz in all_subzones:
    # Filter out all companies in the subzone
    subzone_companies = company_by_subzone.loc[company_by_subzone['subzone_name'] == sz, subzone_columns]
    subzone_companies['primary_ssic_str'] = company_by_subzone['primary_ssic_code'].apply(ssic_cleaner)
    
    # Create a frequency table and convert to fraction of all companies
    subzone_freq = subzone_companies.groupby(['primary_ssic_str'])['entity_name'].count().reset_index(name='Count')
    
    # Merge national level sector data with subzone sector data
    p_data_table = subzone_freq.merge(sector_national_count[['primary_ssic_str','live companies']], how = 'left', on = 'primary_ssic_str' )
    
    # Calculate probabilities
    p_data_table['sz_p'] = p_data_table['Count']/p_data_table['live companies']
    p_data_table['subzone'] = sz
    
    # Attach all probabilities to a larger daatset
    sector_distribution_data = pd.concat([sector_distribution_data, p_data_table])

sector_distribution_data.to_csv('sg_sector_distribution_data.csv')

# Set up lists/arrays to correlate and measure co-occurrence
subzone_p_data = pd.read_csv('sg_sector_distribution_data.csv')

# Create lists of sectors and subzones to iterate through
sectors = list(subzone_p_data['primary_ssic_str'].unique())
subzones = list(subzone_p_data['subzone'].unique())

# Create a list of probabilities for each sector
p_list_dict = {}

for sect in sectors:
    p_list_dict[sect] = []

tracker = 0
total_sectors = str(len(sectors))

for sect in sectors:
    tracker += 1 
    for sz in subzones:
        # Pull out probability for companies of the specified sector to appear in the specified subzone
        sect_df = subzone_p_data.loc[(subzone_p_data['primary_ssic_str'] == sect) & (subzone_p_data['subzone'] == sz), ['sz_p']]
        
        if len(sect_df) > 0:
            p = sect_df['sz_p'].iloc[0]
            p_list_dict[sect].append(p)
            
        else:
            p = 0
            p_list_dict[sect].append(p)
           
    print(str(tracker) + ' sectors out of ' + total_sectors  + ' sectors completed')

p_df = pd.DataFrame(p_list_dict)
p_df.to_csv('computed_p_sector_in_subzones.csv')

sector_p_data = pd.read_csv('computed_p_sector_in_subzones.csv')
correlation_matrix = sector_p_data.corr()
correlation_df = pd.DataFrame(correlation_matrix)
correlation_df.to_csv('sector_cooccurence_matrix.csv')
