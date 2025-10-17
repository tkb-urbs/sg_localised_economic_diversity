# Import required libraries
import pandas as pd # for managing data frames
import geopandas as gpd # for managing subzone maps
from shapely.geometry import Point # deals with coordinates in csv file
import requests

# Create lists of files required by functions
roads = pd.read_csv('road_by_subzone_cleaned.csv') # this file contains list of all roads in SG and the subzones they run through

geojson_file = 'ura_subzone_boundary.geojson' # download URA subzone boundaries as a geojson from data.gov.sg
geojson_gdf = gpd.read_file(geojson_file)

acra_files = ['ACRAInformationonCorporateEntitiesA.csv',
             'ACRAInformationonCorporateEntitiesB.csv',
             'ACRAInformationonCorporateEntitiesC.csv',
             'ACRAInformationonCorporateEntitiesD.csv',
             'ACRAInformationonCorporateEntitiesE.csv',
             'ACRAInformationonCorporateEntitiesF.csv',
             'ACRAInformationonCorporateEntitiesG.csv',
             'ACRAInformationonCorporateEntitiesH.csv',
             'ACRAInformationonCorporateEntitiesI.csv',
             'ACRAInformationonCorporateEntitiesJ.csv',
             'ACRAInformationonCorporateEntitiesK.csv',
             'ACRAInformationonCorporateEntitiesL.csv',
             'ACRAInformationonCorporateEntitiesM.csv',
             'ACRAInformationonCorporateEntitiesN.csv',
             'ACRAInformationonCorporateEntitiesO.csv',
             'ACRAInformationonCorporateEntitiesP.csv',
             'ACRAInformationonCorporateEntitiesQ.csv',
             'ACRAInformationonCorporateEntitiesR.csv',
             'ACRAInformationonCorporateEntitiesS.csv',
             'ACRAInformationonCorporateEntitiesT.csv',
             'ACRAInformationonCorporateEntitiesU.csv',
             'ACRAInformationonCorporateEntitiesV.csv',
             'ACRAInformationonCorporateEntitiesW.csv',
             'ACRAInformationonCorporateEntitiesX.csv',
             'ACRAInformationonCorporateEntitiesY.csv',
             'ACRAInformationonCorporateEntitiesZ.csv',
             'ACRAInformationonCorporateEntitiesOthers.csv']

# ACRA data is big, so I pull out only columns that interest me
desired_columns =['entity_name',
                 'entity_type_description',
                 'business_constitution_description',
                 'entity_status_description',
                 'registration_incorporation_date',
                 'block',
                 'street_name',
                 'primary_ssic_code',
                 'primary_ssic_description',
                 'primary_user_described_activity',
                 'secondary_ssic_code',
                 'secondary_ssic_description',
                 'secondary_user_described_activity']

# define a function to select roads in subzone
def road_selector(subzone_name):
    subzone_roads = roads[roads['SUBZONE_N'] == subzone_name]
    subzone_roads = list(subzone_roads.RD_NAME.unique()) # need to do this as road dataset includes segments of the same road
    return subzone_roads

# function to get coordinates from OneMap by Shawn Tham
# OneMap API key for geocoding
key = 'your API key'
headers = {'Authorization': key}

def getcoordinates(address):
    req = requests.get('https://www.onemap.gov.sg/api/common/elastic/search?searchVal='+address+'&returnGeom=Y&getAddrDetails=Y&pageNum=1', headers = headers)
    resultsdict = eval(req.text)
    if len(resultsdict['results'])>0:
        return resultsdict['results'][0]['LATITUDE'], resultsdict['results'][0]['LONGITUDE']
    else:
        pass

# define a function to select companies with address on selected roads and geocode them
def subzone_company_selector(subzone_name):
    road_list = road_selector(subzone_name)
    subzone_companies = pd.DataFrame(columns = desired_columns)
    
    for file in acra_files:
        acra_df = pd.read_csv(file, usecols = desired_columns)
        extracted_df = acra_df.loc[acra_df['street_name'].isin(road_list)]
        subzone_companies = pd.concat([subzone_companies,extracted_df])

    # Attach coordinates to companies (the loop and method are also by Shawn Tham)
    subzone_companies['address'] = subzone_companies['block']+ ' '+ subzone_companies['street_name']
    addresslist = subzone_companies['address']
    coordinateslist = []
    count = 0
    failed_count = 0

    # create loop to retrieve coordinates
    for address in addresslist:
        try:
            if len(getcoordinates(address))>0:
                count = count + 1
                print('Extracting',count,'out of',len(addresslist),'addresses')
                coordinateslist.append(getcoordinates(address))
        except:
            count = count + 1
            failed_count = failed_count + 1
            print('Failed to extract',count,'out of',len(addresslist),'addresses')
            coordinateslist.append(None)
    print('Total Number of Addresses With No Coordinates',failed_count)

    # Append coordinates to original data and export as csv
    subzone_companies.reset_index(drop=True, inplace=True)

    df_coordinates = pd.DataFrame(coordinateslist)
    df_combined = subzone_companies.join(df_coordinates)
    df_combined  = df_combined .rename(columns={0:'Latitude', 1:'Longitude'})

    file_name = subzone_name + ".csv"
    df_combined.to_csv(file_name, encoding='utf-8', index=False)
    return file_name

# create a function to isolate subzone from geojson. ensure only companies within subzone get selected
def subzone_clipper(subzone_name, csv_file_name):
    
    # extract geometry of desired subzone
    column_name = 'Description'
    search_string = '<td>' + subzone_name + '<\/td>'
    
    desired_row = geojson_gdf[geojson_gdf[column_name].str.contains(search_string, na=False)]
    
    # bring in company data from csv file
    company_df = pd.read_csv(csv_file_name)
    geometry = [Point(lon, lat) for lon, lat in zip(company_df['Longitude'], company_df['Latitude'])]
    company_gdf = gpd.GeoDataFrame(company_df, geometry=geometry)
    company_gdf.set_crs("EPSG:4326", allow_override=True, inplace=True)

    # clip to subzone
    clipped_gdf = gpd.clip(company_gdf, desired_row.geometry)
    clipped_gdf.to_csv(subzone_name + ' companies.csv', index=False)

# run function with desired subzone in caps e.g. "TAI SENG"
file_name = subzone_company_selector("TAI SENG")
subzone_clipper("TAI SENG", file_name) # you may run this as a nested function if desired
