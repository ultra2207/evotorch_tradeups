import requests
import csv
import json
import urllib.parse
import random
import os
import re
import time
import subprocess
import sys
from tqdm import tqdm
from requests.exceptions import Timeout, RequestException
import numpy as np

# Redirect stderr to the file
with open('zerror_log.txt', 'w') as error_file:
    sys.stderr = error_file

    def format_steam_market_url(item_name):
        encoded_item_name = urllib.parse.quote(item_name)
        return f'https://steamcommunity.com/market/listings/730/{encoded_item_name}/render/'

    def get_server_list():
        try:
            with open('vpn_server_list.csv', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                servers = [(row['server'], float(row['time_score'])) for row in reader]
            return servers
        except FileNotFoundError:
            print("vpn_server_list.csv not found. Please run the server ranking script first.")
            return []

    def change_mullvad_server(server):
        try:
            start_time = time.time()
            with open('.temp/zlog.txt', 'a') as log_file:
                subprocess.run(["mullvad", "relay", "set", "location", server], check=True, stdout=log_file, stderr=log_file)
                subprocess.run(["mullvad", "connect"], check=True, stdout=log_file, stderr=log_file)
            time.sleep(4)
            while True:
                status = subprocess.run(["mullvad", "status"], capture_output=True, text=True, check=True)
                if f"Connected to {server}" in status.stdout:
                    end_time = time.time()
                    connection_time = end_time - start_time
                    return connection_time
                elif "Connecting" not in status.stdout or time.time() - start_time > 5:
                    return False
                
                time.sleep(0.3)
        except subprocess.CalledProcessError as e:
            with open('.temp/zlog.txt', 'a') as log_file:
                log_file.write(f"Error changing Mullvad server: {e}\n")
                log_file.write("Command output:\n")
                log_file.write(e.output)
            return False

    def fetch_data(item_name, pbar):
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        headers = {
            'Accept': 'text/javascript, text/html, application/xml, text/xml, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Referer': 'https://steamcommunity.com/market/',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': ua,
        }

        params = {
            'query': '',
            'start': '0',
            'count': '100',
            'language': 'english',
            'currency': '24',
            'norender': 1,
        }

        formatted_url = format_steam_market_url(item_name)
        try:
            with requests.Session() as session:
                response = session.get(formatted_url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('app_data', {}).get('730', {}).get('appid') == 730:
                    sanitized_item_name = re.sub(r'[\\/*?:"<>|]', '', item_name)
                    os.makedirs('steamjsons', exist_ok=True)
                    with open(f'steamjsons/{sanitized_item_name}_data.json', 'w', encoding='utf-8') as json_file:
                        json.dump(data, json_file, ensure_ascii=False, indent=4)

                    pbar.update(1)
                    time.sleep(random.uniform(0.1, 0.3))
                    return True
            return False
        except (Timeout, RequestException) as e:
            print(f"Error fetching data for {item_name}: {e}")
            return False

    def weighted_random_choice(servers):
        servers, time_scores = zip(*servers)
        weights = [1 / score for score in time_scores]  # Invert scores so lower scores have higher weight
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]
        return np.random.choice(servers, p=normalized_weights)

    def main():
        with open('steamnames.txt', 'r', encoding='utf-8') as infile:
            hash_names = [line.strip() for line in infile]

        servers = get_server_list()
        if not servers:
            print("No servers found in vpn_server_list.csv. Please run the server ranking script first.")
            return

        print(f"Processing with {len(hash_names)} items...")

        current_server = weighted_random_choice(servers)
        if not change_mullvad_server(current_server):
            print(f"Failed to connect to initial server {current_server}. Exiting.")
            return

        with tqdm(total=len(hash_names), desc="Processing", file=sys.stdout) as pbar:
            while hash_names:
                item_name = hash_names[0]
                if fetch_data(item_name, pbar):
                    hash_names.pop(0)
                else:
                    # Request failed or timed out, switch to a new server
                    current_server = weighted_random_choice(servers)
                    if not change_mullvad_server(current_server):
                        print(f"Failed to connect to server {current_server}. Trying another.")
                        continue

        pbar.close()
        print("All items processed.")

    if __name__ == "__main__":
        main()

sys.stderr = sys.__stderr__