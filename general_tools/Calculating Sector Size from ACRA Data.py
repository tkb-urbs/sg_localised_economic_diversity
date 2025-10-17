import pandas as pd

# Create list of all 5-digit SSIC codes
ssic = pd.read_csv('ssic2020-classification-structure.csv')
ssic['SSIC_2020_str'] = ssic['SSIC 2020'].apply(str)

five_digit_ssic = []
all_ssic = list(ssic['SSIC_2020_str'])

for code in all_ssic:
    if len(code)==5:
        five_digit_ssic.append(code)

# List out all files we will use and the columns we want from them
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

desired_columns =['entity_status_description',
                 'primary_ssic_code']

# define a function to ensure ACRA data ssic codes that should start with 0, start with 0
def ssic_cleaner(code):
    new_code = str(code)
    if len(new_code) < 5:
        final_code = '0' + new_code
    else:
        final_code = new_code
    return final_code

# Set up lists to store counts of companies
all_companies = []
live_companies = []
done = 0 # This helps to track how many sectors have been counted
subset = five_digit_ssic[0:len(five_digit_ssic)]

for code in subset:
    # These variables store values for the number of all companies that have registered with ACRA and live companies respectively
    # Reset these variables to 0 when starting counting for the next sector
    total_count = 0
    total_live_count = 0
    
    for file in acra_files:
        temp_df = pd.read_csv(file, usecols = desired_columns)
        temp_df['primary_ssic_code_str'] = temp_df['primary_ssic_code'].apply(ssic_cleaner) # Convert everything to a string to avoid issues with the ssic starting with 0
        
        # Count all companies that have registered or attempted registration
        count_df = temp_df[temp_df['primary_ssic_code_str'] == code]
        file_count = count_df.shape[0]
        total_count += file_count
      
        # Count all live companies in sector
        live_df = count_df[count_df['entity_status_description'].isin(['Live','Live Company'])]
        file_live_count = live_df.shape[0]
        total_live_count += file_live_count

    all_companies.append(total_count)
    live_companies.append(total_live_count)
    done += 1
    print(str(done) + ' subsector done')

summary = {'ssic': subset, 'all companies': all_companies, 'live companies': live_companies}
company_count = pd.DataFrame(summary)

company_count.to_csv('sg_sector_count.csv')
