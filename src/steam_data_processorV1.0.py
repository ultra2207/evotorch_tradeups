import csv
import aiohttp
import asyncio
import random
from fake_useragent import UserAgent
from tqdm import tqdm


MAX_ASYNC=50

class CSVWriterQueue:
    def __init__(self, file_path):
        self.file_path = file_path
        self.queue = asyncio.Queue()

    async def write_row(self, row):
        await self.queue.put(row)

    async def process_queue(self):
        while True:
            row = await self.queue.get()
            if row is None:
                break  # Signal to stop processing the queue

            with open(self.file_path, 'a', newline='', encoding='utf-8') as processed_csv_file:
                csv_writer = csv.writer(processed_csv_file)
                csv_writer.writerow(row)




async def get_proxies():
    with open('proxies.txt', 'r') as proxy_file:
        proxies = proxy_file.read().splitlines()
    return proxies

async def get_floatvalue(inspect_link, proxies):
    user_agent = UserAgent()
    random_user_agent = user_agent.random

    headers = {
        'authority': 'api.csfloat.com',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'no-cache',
        'origin': 'https://csfloat.com',
        'pragma': 'no-cache',
        'referer': 'https://csfloat.com/',
        'sec-fetch-site': 'same-site',
        'user-agent': random_user_agent,
    }

    # Select a random proxy
    proxy =random.choice(proxies)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.csfloat.com/?url=' + inspect_link, headers=headers, timeout=10) as response:
                if response.status == 200:
                    # Load the response content as JSON
                    response_json = await response.json()
                    floatvalue = response_json.get('iteminfo', {}).get('floatvalue')
                    return floatvalue
                else:
                    print(f"Error {response.status}")
                    return None
    except Exception as e:
        # Handle client exception
        print(f"{e}")
        return None

async def process_rows(part, proxies, csv_writer_queue,progress_bar):

        while part:
            row_index = random.randrange(len(part))
            row = part[row_index]
            name, inspect_link, collection, price_inr, listing_id, asset_id = row
            floatvalue = await get_floatvalue(inspect_link, proxies)
            if floatvalue is not None:
                # Assuming successful processing means removing from the list
                part.pop(row_index)
                await csv_writer_queue.write_row([name, inspect_link, collection, price_inr, floatvalue,  listing_id, asset_id])
                progress_bar.update(1)


async def main():

    processed_csv = 'steam_data_processed.csv'

    header = ['Name', 'Inspect Link', 'Collection', 'Price (INR)', 'floatvalue', 'Listing ID', 'Asset ID']

    with open(processed_csv, 'a', newline='', encoding='utf-8') as file:
        csv_writer = csv.writer(file)
        #csv_writer.writerow(header)

    # Read the original CSV file
    csv_file_path = 'steam_data.csv'
    csv_writer_queue = CSVWriterQueue('steam_data_processed.csv')
    # Read proxies from the file
    proxies = await get_proxies()

    with open(csv_file_path, 'r', encoding='utf-8') as csv_file:
        csv_reader = list(csv.reader(csv_file))
        
        header = csv_reader.pop(0)  # Get and remove the header
        header.append('floatvalue')
        # Set the number of parts
        num_parts=min(MAX_ASYNC,len(csv_reader)//2)
        # Split the rows into parts based on the number of parts
        parts = [csv_reader[i:i + len(csv_reader) // num_parts] for i in range(0, len(csv_reader), len(csv_reader) // num_parts)]

        # Start the queue processing coroutine
        queue_processing_task = asyncio.create_task(csv_writer_queue.process_queue())

        with tqdm(total=len(csv_reader)-1, desc="Processing Rows") as pbar:
            # Use asyncio.gather to run process_rows concurrently for each part
            tasks = [process_rows(part, proxies, csv_writer_queue, pbar) for part in parts]
            await asyncio.gather(*tasks)
        # Signal the queue processing coroutine to stop
        await csv_writer_queue.write_row(None)
        await queue_processing_task

    print("Processing completed. Check steam_data_processed.csv")

if __name__ == "__main__":
    asyncio.run(main())
