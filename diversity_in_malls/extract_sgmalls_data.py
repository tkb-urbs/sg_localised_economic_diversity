# -*- coding: utf-8 -*-
"""
Created on Mon Oct 13 13:23:02 2025

@author: tkbean
"""

import requests
from bs4 import BeautifulSoup
import json
import pandas as pd

# Create headers for web requests
headers = {
    'User-Agent': #insert your user agent here
}

# define a function to request for source code of website and parse it
def html_requester(url):
    try:
        #Send the GET request
        response = requests.get(url, headers=headers, timeout=10)

        #Check the status code
        if response.status_code == 200:
            # Extract the HTML content
            html_content = response.text
            results = BeautifulSoup(html_content, "html.parser")
            
            return results

        else:
            print(f"Failed to retrieve the webpage. Status code: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the request: {e}")
        
# Extract list of all mall directories
mall_data = html_requester('https://singmalls.app/en/malls')

# find all the links to the directories
mall_dir = list(mall_data.find_all('a', href = True))

# Create list of directories to perform requests on
directories = []

for link in mall_dir: 
    half_link = link.get('href')
    full_link = 'https://singmalls.app/' + half_link
    
    directories.append(full_link)

dir_cleaned = directories[1:107]


# Extract a list of shops from each directory, run through each shop and extract details
# create empty lists to store data
shop_name = []
unit_no = []
mall_name = []
blk_street = []
postal_code = []
open_days = []
open_hours = []
category = []
latitude = []
longitude = []
dir_count = 0

# loop through directories and each shop in each directory
for directory in dir_cleaned:
    all_shop_data = html_requester(directory)
    all_shop_links = list(all_shop_data.find_all('a', href = True))
    
    shop_links = []

    for link in all_shop_links: 
        half_link = link.get('href')
        full_link = 'https://singmalls.app' + half_link
        
        shop_links.append(full_link)
        
    shop_links_cleaned = shop_links[4:len(shop_links)-13]
    
    for shop in shop_links_cleaned:
        the_shop = html_requester(shop)
        
        # Pull out brand name
        shop_title = the_shop.find('h2')
        shop_title_cleaned = shop_title.get_text(strip=True)
        shop_name.append(shop_title_cleaned)
        
        # Pull out address information
        address = list(the_shop.select('div.LocationDetails_container__B7z1S p'))
        
        unit = address[0].get_text(strip=True)
        unit_no.append(unit)
        
        mall_title = address[1].get_text(strip=True)
        mall_name.append(mall_title)
        
        street = address[2].get_text(strip=True)
        blk_street.append(street)
        
        postal = address[3].get_text(strip=True)
        postal_code.append(postal)
        
        # Pull out opening hours information
        opening_hours = the_shop.select('div.MerchantOpeningHours_container__fLhng p')
        
        if len(opening_hours) > 1: 
            days = (opening_hours[0].get_text(strip=True))[:-1]
            open_days.append(days)
        
            hours = opening_hours[1].get_text(strip=True)
            open_hours.append(hours)
        
        else:
            open_days.append('na')
            open_hours.append('na')
        
        # Extract shop category
        category_tag = the_shop.find('h5', string='Category')
        
        if category_tag:
            category_p_tag = category_tag.find_next_sibling('p')

            if category_p_tag:
                category_text = category_p_tag.get_text()
                category.append(category_text)

            else:
                print("Could not find the <p> tag after <h5>Category</h5>.")
                category.append('na')
        else:
            print("Could not find the <h5>Category</h5> element.")
            category.append('na')
        
        # Extract coordinates
        script_tag = the_shop.find('script', id='__NEXT_DATA__')

        if script_tag:
            # Extract the raw JSON string from the tag's contents
            json_data_string = script_tag.string

            # Parse the JSON string into a Python dictionary
            data = json.loads(json_data_string)

            # Navigate the dictionary structure to find the coordinates
            try:
                geo_data = data['props']['pageProps']['schema']['geo']
                
                lat = geo_data['latitude']
                latitude.append(lat)
                
                long = geo_data['longitude']
                longitude.append(long)
                
            except KeyError as e:
                print(f"Error: Could not find key in JSON structure: {e}")
                latitude.append('na')
                longitude.append('na')
                
        else:
            print("Error: Could not find the script tag with id='__NEXT_DATA__'")
            latitude.append('na')
            longitude.append('na')
            
    dir_count += 1
    print(str(dir_count) + ' directories out of ' + str(len(dir_cleaned)) + ' completed!')

malls_dict = {'shop_name':shop_name,
              'unit_no':unit_no,
              'mall':mall_name,
              'street': blk_street,
              'postal_code': postal_code,
              'typ_day': open_days,
              'typ_opening_hours': open_hours,
              'category': category ,
              'latitude': latitude,
              'longitude': longitude}

reit_mall_directories = pd.DataFrame(malls_dict)
reit_mall_directories.to_csv('reit_mall_shops.csv')
