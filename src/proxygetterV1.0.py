import requests
from tqdm import tqdm
import subprocess
import shutil
import os
import platform
import ctypes


# URLs of the specific files you want to download
file_urls = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/main/http.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/main/socks4.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/main/socks5.txt"
]

# Create the .temp directory if it does not exist
if not os.path.exists('.temp'):
    os.makedirs('.temp')

# Download the specific files using curl
for url in file_urls:
    file_name = os.path.basename(url)
    subprocess.run(["curl", "-o", f".temp/{file_name}", url])



headers = {
    'authority': 'proxylist.geonode.com',
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.9',
    'cache-control': 'no-cache',
    'origin': 'https://geonode.com',
    'pragma': 'no-cache',
    'referer': 'https://geonode.com/',
    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

# Initialize a set for proxies
all_proxies = set()

for page in tqdm(range(1, 11), desc="Fetching pages"):
    params = {
        'limit': '500',
        'page': str(page),
        'sort_by': 'lastChecked',
        'sort_type': 'desc',
    }

    response = requests.get('https://proxylist.geonode.com/api/proxy-list', params=params, headers=headers)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the JSON content
        json_content = response.json()

        # Extract IPs and add to the all_proxies set
        for proxy in json_content['data']:
            all_proxies.add(f"{proxy['ip']}:{proxy['port']}")

    else:
        print(f"Failed to retrieve data for page {page}. Status code: {response.status_code}")

# Write the set to proxies.txt to eliminate duplicates
with open('proxies.txt', 'w', encoding='utf-8') as file:
    for proxy in all_proxies:
        file.write(f"{proxy}\n")

print("All pages fetched. Updated proxies written to proxies.txt")


# Read the content of the existing proxies.txt file into a set
existing_proxy_set = set()

with open("proxies.txt", "r") as existing_file:
    existing_proxies = existing_file.read().splitlines()
    existing_proxy_set.update(existing_proxies)

# Read the content of the files from the downloaded files and create a set
new_proxy_set = set()

file_names = ["http.txt", "socks4.txt", "socks5.txt"]

for file_name in file_names:
    with open(f".temp/{file_name}", "r") as file:
        proxies = file.read().splitlines()
        new_proxy_set.update(proxies)

# Combine the two sets
combined_proxy_set = existing_proxy_set.union(new_proxy_set)

# Write the combined set to proxies.txt
with open("proxies.txt", "w") as output_file:
    for proxy in combined_proxy_set:
        output_file.write(proxy + "\n")

def delete_temp_folder(folder_path):
    try:
        # Check if the folder exists
        if os.path.exists(folder_path):
            # On Windows, use ctypes to run the command with administrative privileges
            if platform.system() == 'Windows':
                ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", f"/c rmdir /s /q \"{folder_path}\"", None, 1)
            else:
                shutil.rmtree(folder_path)

            print(f"The folder '{folder_path}' has been successfully deleted.")
        else:
            print(f"The folder '{folder_path}' does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")

temp_folder_path = os.path.join(os.getcwd(), ".temp")
delete_temp_folder(temp_folder_path)

print("Successfully read, combined, and updated proxy lists and .temp folder deleted.")
