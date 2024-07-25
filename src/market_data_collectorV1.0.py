import requests
import urllib.parse
import json
import csv
import time
import random
from tqdm import tqdm
import re

def get_market_data(market_hash_name):
    cookies = {
        'ActListPageSize': '10',
        'timezoneOffset': '19800,0',
        'browserid': '2684757052209436603',
        'recentlyVisitedAppHubs': '431960',
        'steamCurrencyId': '24',
        'steamLoginSecure': '76561199557379295%7C%7CeyAidHlwIjogIkpXVCIsICJhbGciOiAiRWREU0EiIH0.eyAiaXNzIjogInI6MERFNl8yM0FCQ0REOF8yOUVEQSIsICJzdWIiOiAiNzY1NjExOTk1NTczNzkyOTUiLCAiYXVkIjogWyAid2ViIiBdLCAiZXhwIjogMTcwMzQxNjEwMSwgIm5iZiI6IDE2OTQ2ODkyMjMsICJpYXQiOiAxNzAzMzI5MjIzLCAianRpIjogIjBERDlfMjNBQkNEREJfRkIzOTkiLCAib2F0IjogMTcwMzMyOTIyMiwgInJ0X2V4cCI6IDE3MjE1OTcwMTAsICJwZXIiOiAwLCAiaXBfc3ViamVjdCI6ICIxMDQuMjguMjMzLjgyIiwgImlwX2NvbmZpcm1lciI6ICIxMDQuMjguMjMzLjgyIiB9.-NVh9uSmEqFc75SZmy2sMHu-7uotuWlWYtWkjU7O3ZO1Y2O326N9EVfSMM-aE7c8lwQnW_f2qbo_IyjvvzYdAg',
        'sessionid': '85cce5bde1ea4f7e7ae1a81b',
        'webTradeEligibility': '%7B%22allowed%22%3A1%2C%22allowed_at_time%22%3A0%2C%22steamguard_required_days%22%3A15%2C%22new_device_cooldown_days%22%3A0%2C%22time_checked%22%3A1703393155%7D',
    }

    headers = {
        'Accept': 'text/javascript, text/html, application/xml, text/xml, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        # 'Cookie': '... (unchanged)',
        'Pragma': 'no-cache',
        'Referer': f'https://steamcommunity.com/market/search?appid=730&q={market_hash_name}',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'X-Prototype-Version': '1.7',
        'X-Requested-With': 'XMLHttpRequest',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    response = requests.get(
        f'https://steamcommunity.com/market/search/render/?query={market_hash_name}&start=10&count=10&search_descriptions=0&sort_column=default&sort_dir=desc&appid=730',
        cookies=cookies,
        headers=headers,
    )

    return response


with open('skins.csv', 'r', encoding='utf-8') as csv_file:
    reader = csv.reader(csv_file)
    next(reader)  # Skip the header
    market_hash_names = [row[1] for row in reader]

# Open the output files
csv_file = open('searched_market_data.csv', 'w', newline='', encoding='utf-8')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(['hash_name', 'sell_listings', 'sell_price'])  # Add header

def clean_and_convert_sell_price(result):
    sell_price_str = result.get('sell_price', '0')
    # Use regex to remove anything that's not a digit or a dot
    clean_sell_price_str = re.sub(r'[^0-9.]', '', sell_price_str)
    # Convert the cleaned string to float
    sell_price = float(clean_sell_price_str) if clean_sell_price_str else 0.0
    return sell_price

# Create a tqdm progress bar
progress_bar = tqdm(total=len(market_hash_names), unit='items')

wear_conditions = ["Factory New", "Minimal Wear", "Field-Tested", "Well-Worn", "Battle-Scarred"]

def clean_and_convert_sell_price(result):
    sell_price_str = result.get('sell_price_text', '0')
    # Use regex to remove anything that's not a digit or a dot
    clean_sell_price_str = re.sub(r'[^0-9.]', '', sell_price_str)
    # Convert the cleaned string to float
    sell_price = float(clean_sell_price_str) if clean_sell_price_str else 0.0
    return sell_price

# Iterate through each market_hash_name
for market_hash_name in market_hash_names:
    # Flag to indicate if the request was successful
    success = False
    c=0
    while not success:
        
        try:
            cookies = {
                'ActListPageSize': '10',
                'timezoneOffset': '19800,0',
                'browserid': '2684757052209436603',
                'recentlyVisitedAppHubs': '431960',
                'steamCurrencyId': '24',
                'sessionid': '85cce5bde1ea4f7e7ae1a81b',
                'webTradeEligibility': '%7B%22allowed%22%3A1%2C%22allowed_at_time%22%3A0%2C%22steamguard_required_days%22%3A15%2C%22new_device_cooldown_days%22%3A0%2C%22time_checked%22%3A1703393155%7D',
                'steamCountry': 'IN%7C700e95acfe16519091c5ed3a7b65c54f',
                'steamLoginSecure': '76561199557379295%7C%7CeyAidHlwIjogIkpXVCIsICJhbGciOiAiRWREU0EiIH0.eyAiaXNzIjogInI6MERFNl8yM0FCQ0REOF8yOUVEQSIsICJzdWIiOiAiNzY1NjExOTk1NTczNzkyOTUiLCAiYXVkIjogWyAid2ViIiBdLCAiZXhwIjogMTcwMzUwNDQ0MCwgIm5iZiI6IDE2OTQ3NzY3MjIsICJpYXQiOiAxNzAzNDE2NzIyLCAianRpIjogIjBERDlfMjNBQkNERUFfMkNBNjciLCAib2F0IjogMTcwMzMyOTIyMiwgInJ0X2V4cCI6IDE3MjE1OTcwMTAsICJwZXIiOiAwLCAiaXBfc3ViamVjdCI6ICIxMDQuMjguMjMzLjgyIiwgImlwX2NvbmZpcm1lciI6ICIxMDQuMjguMjMzLjgyIiB9.4WvH2yhwsrTAEsOZjIFBbr2fIZJoDOm9rFID_43n-6o6M8Z-6UycQ3AXkJchsaQXL_nxXP-ej4-rFgKOYZ1nCQ',
            }

            headers = {
                'Accept': 'text/javascript, text/html, application/xml, text/xml, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                # 'Cookie': 'ActListPageSize=10; timezoneOffset=19800,0; browserid=2684757052209436603; recentlyVisitedAppHubs=431960; steamCurrencyId=24; sessionid=85cce5bde1ea4f7e7ae1a81b; webTradeEligibility=%7B%22allowed%22%3A1%2C%22allowed_at_time%22%3A0%2C%22steamguard_required_days%22%3A15%2C%22new_device_cooldown_days%22%3A0%2C%22time_checked%22%3A1703393155%7D; steamCountry=IN%7C700e95acfe16519091c5ed3a7b65c54f; steamLoginSecure=76561199557379295%7C%7CeyAidHlwIjogIkpXVCIsICJhbGciOiAiRWREU0EiIH0.eyAiaXNzIjogInI6MERFNl8yM0FCQ0REOF8yOUVEQSIsICJzdWIiOiAiNzY1NjExOTk1NTczNzkyOTUiLCAiYXVkIjogWyAid2ViIiBdLCAiZXhwIjogMTcwMzUwNDQ0MCwgIm5iZiI6IDE2OTQ3NzY3MjIsICJpYXQiOiAxNzAzNDE2NzIyLCAianRpIjogIjBERDlfMjNBQkNERUFfMkNBNjciLCAib2F0IjogMTcwMzMyOTIyMiwgInJ0X2V4cCI6IDE3MjE1OTcwMTAsICJwZXIiOiAwLCAiaXBfc3ViamVjdCI6ICIxMDQuMjguMjMzLjgyIiwgImlwX2NvbmZpcm1lciI6ICIxMDQuMjguMjMzLjgyIiB9.4WvH2yhwsrTAEsOZjIFBbr2fIZJoDOm9rFID_43n-6o6M8Z-6UycQ3AXkJchsaQXL_nxXP-ej4-rFgKOYZ1nCQ',
                'Pragma': 'no-cache',
                'Referer': 'https://steamcommunity.com/market/search?q=R8+Revolver',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'X-Prototype-Version': '1.7',
                'X-Requested-With': 'XMLHttpRequest',
                'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
            }

            params = {
                'query': market_hash_name,
                'start': '0',
                'count': '10',
                'search_descriptions': '0',
                'sort_column': 'default',
                'sort_dir': 'desc',
                'appid': '730',
                'norender': 1,
                'currency': 24
            }
                
            response = requests.get('https://steamcommunity.com/market/search/render/', params=params, cookies=cookies, headers=headers)

            if response.status_code == 200:
                # Parse the JSON response
                data = response.json()

                # Find the result with the matching hash_name
                matching_result = None

                found_conditions = {condition: False for condition in wear_conditions}
                
                for result in data.get('results', []):

                    # Check if 'hash_name' is present in the result
                    if 'hash_name' not in result:
                        print("Error: 'hash_name' is missing in a result.")
                        # Handle the error appropriately, e.g., return or raise an exception
                        matching_result = None

                    for condition in wear_conditions:
                        if f"{market_hash_name} ({condition})" in result['hash_name']:

                            matching_result = result
                            found_conditions[condition] = True
                            hash_name = result.get('hash_name', '')
                            sell_listings = result.get('sell_listings', 0)
                            sell_price = clean_and_convert_sell_price(result) # Convert to dollars
                            csv_writer.writerow([hash_name, sell_listings, sell_price])
                            csv_file.flush()
                
                missing_wears = [condition for condition, found in found_conditions.items() if not found]
                
                if missing_wears:
                    if market_hash_name != 'MAC-10 | Sakkaku':
                        print(f"Missing {market_hash_name} ({', '.join(missing_wears)})")
                                            

                if matching_result:
                    success = True
                    progress_bar.update(1)
                    delay = random.uniform(2,7)                
                    time.sleep(delay)
                    
                else:                 
                    wait_time = random.uniform(5,10)
                    time.sleep(wait_time)
                    c+=1
                    if(c==8):
                        success = True 
                        message = f"{market_hash_name}\n"
                        with open("failed.txt", "a") as failed_file:
                            failed_file.write(message)
                
            elif response.status_code == 429:
                print("Rate limited (429) - Retrying after waiting...")
                wait_time = random.uniform(30, 45)
                time.sleep(wait_time)
            elif response.status_code == 500:
                print(f"HTTP Status Code 500 - Internal Server Error for hash_name: {market_hash_name}")
                break
            else:
                pass

        except Exception as e:
            print(e)
            wait_time = random.uniform(15,30)
            time.sleep(wait_time)

csv_file.close()
progress_bar.close()
print('all done.')