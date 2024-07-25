import os
import json
import csv
import re

def replace_placeholders(link, listing_id, asset_id):
    return link.replace("%listingid%", listing_id).replace("%assetid%", asset_id)

# Function to preprocess the filename
def preprocess_filename(filename):
    cleaned_filename = filename.replace('_data.json', '')  # Remove '_data.json'
    cleaned_filename = re.sub(r'\([^)]*\)', '', cleaned_filename)  # Remove content within parentheses
    cleaned_filename = cleaned_filename.replace('StatTrak™', '')  # Remove 'StatTrak™'
    cleaned_filename = cleaned_filename.replace('Souvenir', '')  # Remove 'Souvenir'
    cleaned_filename = cleaned_filename.strip()  # Strip leading/trailing whitespaces
    return cleaned_filename

# Read skins.csv into a dictionary
skins_dict = {}
with open('skins.csv', 'r', encoding='utf-8') as skins_file:
    skins_reader = csv.reader(skins_file)
    for row in skins_reader:
        skins_dict[row[1]] = row[0]

# Create steam_data.csv
with open('steam_data.csv', 'w', newline='', encoding='utf-8') as steam_data_file:
    steam_data_writer = csv.writer(steam_data_file)
    steam_data_writer.writerow(['Name', 'Inspect Link', 'Collection', 'Price (INR)', 'Listing ID', 'Asset ID'])

    # Iterate over all JSON files in the steamjsons folder
    for filename in os.listdir('steamjsons'):
        if filename.endswith('.json'):
            file_path = os.path.join('steamjsons', filename)

            # Read JSON data from the file
            with open(file_path, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)
                
            if data['total_count'] == 0:
                continue  # Skip to the next file if total_count is 0

            # Inside the loop
            found_match = None

            # Preprocess the filename
            cleaned_filename = preprocess_filename(filename)

            # Find the exact matching item in skins.csv
            for skin_filename, skin_name in skins_dict.items():
                if cleaned_filename.lower().strip() == skin_filename.replace(' | ', '  ').lower().strip():
                    found_match = skin_name
                    break

            for item_id, item_data in data['listinginfo'].items():
                listing_id = item_data['listingid']
                asset_id = item_data['asset']['id']
                inspect_link = replace_placeholders(item_data['asset']['market_actions'][0]['link'], listing_id, asset_id)

                # Check if 'converted_price' key exists in the item_data
                if 'converted_price' in item_data:
                    converted_price_inr = item_data['converted_price'] / 86.95653
                    steam_data_writer.writerow([filename, inspect_link, found_match, converted_price_inr, listing_id, asset_id])
                else:
                    # Handle the case where 'converted_price' key is not present
                    print(f"Warning: 'converted_price' not found for {filename}")

print("Process completed successfully.")
