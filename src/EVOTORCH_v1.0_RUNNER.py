import json
import subprocess
import math

# Set the number of parallel processes
PARALLELIZATION = 7

# Read the processed_items.json file
with open('processed_items.json', 'r') as file:
    processed_items = json.load(file)

total_items = len(processed_items)

# Calculate the size of each chunk
chunk_size = math.ceil(total_items / PARALLELIZATION)

# Create the commands for each parallel process
commands = []
for i in range(PARALLELIZATION):
    start_index = i * chunk_size
    end_index = min((i + 1) * chunk_size, total_items)
    
    if start_index >= total_items:
        break
    
    command = f'python EVOTORCH_V1.0.py {start_index} {end_index}'
    commands.append(command)

# Function to run a command in a new cmd window
def run_command(command):
    subprocess.Popen(f'start cmd /K {command}', shell=True)

# Run each command in a new cmd window
for command in commands:
    run_command(command)
    print(f"Started: {command}")

print(f"Launched {len(commands)} parallel processes.")

# End of script
# EVOTORCH_v1.0_RUNNER.py

