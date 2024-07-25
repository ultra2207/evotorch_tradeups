import subprocess
import csv
import json
import urllib.parse
import random
import os
import re
import time
import requests

def format_steam_market_url(item_name):
    encoded_item_name = urllib.parse.quote(item_name)
    return f'https://steamcommunity.com/market/listings/730/{encoded_item_name}/render/'

def get_mullvad_servers():
    try:
        result = subprocess.run(["mullvad", "relay", "list"], capture_output=True, text=True, check=True)
        output = result.stdout

        # Simplified regex to find server names with three inner dashes
        server_pattern = re.compile(r'\b(\S+-\S+-\S+-\S+)\b')
        servers = server_pattern.findall(output)
        
        if not servers:
            print("No servers detected. Here's the raw output:")
            print(output)
            return []

        print(f"Detected {len(servers)} servers")
        return servers
    except subprocess.CalledProcessError as e:
        print(f"Error running 'mullvad relay list': {e}")
        print("Command output:")
        print(e.output)
        return []
    except Exception as e:
        print(f"Unexpected error in get_mullvad_servers: {e}")
        return []

def change_mullvad_server(server):
    try:
        
        subprocess.run(["mullvad", "relay", "set", "location", server], check=True)
        subprocess.run(["mullvad", "connect"], check=True)
        s_t = time.time()
        time.sleep(4)
        
        while True:
            status = subprocess.run(["mullvad", "status"], capture_output=True, text=True, check=True)
            if f"Connected to {server}" in status.stdout:
                e_t = time.time()
                connection_time = e_t - s_t
                print(f"Successfully connected to {server} in {connection_time:.2f} seconds")
                return connection_time
            elif "Connected" not in status.stdout or time.time() - s_t > 6:
                print(f"Failed to connect to {server} within 5 seconds")
                return float('inf')
            
            time.sleep(0.1)

    except subprocess.CalledProcessError as e:
        print(f"Error changing Mullvad server: {e}")
        print("Command output:")
        print(e.output)
        return float('inf')

def measure_server_performance(server, item_name):
    connection_time = change_mullvad_server(server)
    if connection_time == float('inf'):
        return (server, float('inf'))

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
    total_time = 0

    for _ in range(3):
        try:
            start_time = time.time()
            response = requests.get(formatted_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            total_time += time.time() - start_time
        except requests.RequestException as e:
            print(f"Error fetching data for {item_name} on server {server}: {e}")
            return (server, float('inf'))

    time_score = total_time * 5 + connection_time
    print(f'time_score: {time_score}')
    return (server, time_score)

def main():
    servers = get_mullvad_servers()
    if not servers:
        print("No Mullvad servers detected. Please check your Mullvad VPN installation and connection.")
        return

    with open('steamnames.txt', 'r', encoding='utf-8') as infile:
        hash_names = [line.strip() for line in infile]

    print("Ranking servers based on performance. This may take a few minutes...")
    sorted_servers = []
    random.shuffle(servers)
    for server in servers:
        print(f"Testing server: {server}")
        item_name = random.choice(hash_names)
        server_performance = measure_server_performance(server, item_name)
        sorted_servers.append(server_performance)

    sorted_servers.sort(key=lambda x: x[1])

    print("Servers ranked. Writing to vpn_server_list.csv...")
    with open('vpn_server_list.csv', 'w', newline='') as csvfile:
        fieldnames = ['server', 'time_score']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for server, time_score in sorted_servers:
            writer.writerow({'server': server, 'time_score': time_score})

    print("vpn_server_list.csv has been created.")

if __name__ == "__main__":
    main()