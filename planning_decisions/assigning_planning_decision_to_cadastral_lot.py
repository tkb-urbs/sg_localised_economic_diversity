import pandas as pd
import geopandas as gpd

# Load Planning Decision Data
df = pd.read_csv("Planning_Decisions.csv")

# Clean data such that each row reflects one cadastral lot and the data that occurs on it
lots = df['mkts_lotno'].to_list()

new_df_columns = ['decision_date', 
                  'address', 
                  'submission_desc', 
                  'decision_type', 
                  'appl_type', 
                  'mkts_lotno', 
                  'dr_id', 
                  'submission_no', 
                  'decision_no',
                  'Latitude',
                  'Longitude',
                  'LOT_KEY']

new_df = pd.DataFrame(columns = new_df_columns) # Initialise new data frame to contain separated data

row_no = 0

for l in lots:
    l = str(l)
    split_parcels = l.split(',')
    
    for parcel in split_parcels:
        new_row = list(df.loc[row_no])
        new_row.append(parcel)
        new_df.loc[len(new_df)] = new_row

    row_no += 1

lots = new_df['LOT_KEY'].to_list()
modified_lots = []

for lot in lots:
    modified_lot = lot.replace(" ", "-")
    first = modified_lot[0:1]

    if  first == "-":
        modified_lot = modified_lot[1:]
        modified_lots.append(modified_lot)
    
    else:
        modified_lots.append(modified_lot)

new_df = new_df.drop('LOT_KEY', axis = 1)

new_df['LOT_KEY'] = modified_lots

gdf = gpd.read_file('cadastral_map.geojson')

lot_geom = gdf[['LOT_KEY','geometry']].copy()

merged_df = pd.merge(new_df,
                     lot_geom,
                     on = 'LOT_KEY',
                     how='inner')

from datetime import datetime

month = []
year = []

for date in merged_df['decision_date']:
    datetime_str = date
    datetime_obj = datetime.strptime(datetime_str, '%d/%m/%Y')
    
    m = datetime_obj.strftime("%Y/%m")
    month.append(m)
    
    y = datetime_obj.strftime("%Y")
    year.append(y)

merged_df['month'] = month
merged_df['year'] = year

merged_df.to_csv('new_erection_lots.csv')
