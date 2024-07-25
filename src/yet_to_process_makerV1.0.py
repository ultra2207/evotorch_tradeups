import pandas as pd

# Load the CSV files
steam_data = pd.read_csv('steam_data.csv')
zsteam_data_processed = pd.read_csv('steam_data_processed.csv')

# Merge the data on Listing ID, Asset ID, and Inspect Link to find rows that are in steam_data but not in zsteam_data_processed
merged_data = pd.merge(steam_data, zsteam_data_processed, on=['Listing ID', 'Asset ID', 'Inspect Link'], how='left', indicator=True)

# Filter rows that are only in steam_data
yet_to_process = merged_data[merged_data['_merge'] == 'left_only']

# Drop the _merge column
yet_to_process = yet_to_process.drop(columns=['_merge'])

# Save to CSV
yet_to_process.to_csv('yet_to_process.csv', index=False)
