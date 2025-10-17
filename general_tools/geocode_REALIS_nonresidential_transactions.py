import pandas as pd
import requests
import re

comm_trans = pd.read_csv("retail_transactions_combined.csv")

# OneMap API key for geocoding
key = 'your API key'
headers = {'Authorization': key}

# function to get coordinates from OneMap by Shawn Tham
def getcoordinates(address):
    req = requests.get('https://www.onemap.gov.sg/api/common/elastic/search?searchVal='+address+'&returnGeom=Y&getAddrDetails=Y&pageNum=1', headers = headers)
    resultsdict = eval(req.text)
    if len(resultsdict['results'])>0:
        return resultsdict['results'][0]['LATITUDE'], resultsdict['results'][0]['LONGITUDE']
    else:
        pass

# create list of addresses
addresslist_uncleaned = list(comm_trans['Address'])
addresslist = []

for addr in addresslist_uncleaned:
    if '#' in addr:
        addr_cleaned = (re.findall('.+#', addr)[0])[:-2]
        addresslist.append(addr_cleaned)
    else:
        addresslist.append(addr)
    
# create variables to hold coordinate data
coordinateslist = []
count = 0
failed_count = 0

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
comm_trans.reset_index(drop=True, inplace=True)

df_coordinates = pd.DataFrame(coordinateslist)
df_combined = comm_trans.join(df_coordinates)
df_combined  = df_combined .rename(columns={0:'Latitude', 1:'Longitude'})

df_combined.to_csv("commercial_transactions_geocoded.csv", encoding='utf-8', index=False)
