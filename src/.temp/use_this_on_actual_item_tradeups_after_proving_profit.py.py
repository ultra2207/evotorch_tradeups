import pycuda.driver as cuda
import pycuda.autoinit
from pycuda.compiler import SourceModule
import pycuda.gpuarray as gpuarray
import numpy as np
import json
from tqdm import tqdm
import re


# Load data from the JSONL file
data = []
with open('profitable_tradeups.jsonl', 'r') as file:
    for line in file:
        data.append(json.loads(line))

# Constants
num_runs = 100000  # Number of simulation runs
max_steps = 100000  # Maximum number of steps to simulate
profit_threshold = 1.05  # 5% profit threshold

# CUDA kernel
mod = SourceModule("""
__device__ unsigned int wang_hash(unsigned int seed)
{
    seed = (seed ^ 61) ^ (seed >> 16);
    seed *= 9;
    seed = seed ^ (seed >> 4);
    seed *= 0x27d4eb2d;
    seed = seed ^ (seed >> 15);
    return seed;
}

__global__ void simulate_profitability(float *output_prices, int num_prices, float total_input_cost, 
                                       int num_runs, int max_steps, float profit_threshold, int *num_steps_to_profit) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < num_runs) {
        unsigned int seed = idx;
        
        float cumulative_profitability = 1.0f;
        for (int step = 0; step < max_steps; step++) {
            seed = wang_hash(seed);
            int price_idx = seed % num_prices;
            float output_price = output_prices[price_idx];
            float step_profitability = output_price / (total_input_cost * 1.15f);
            cumulative_profitability *= step_profitability;
            if (cumulative_profitability >= profit_threshold) {
                num_steps_to_profit[idx] = step + 1;
                return;
            }
        }
        num_steps_to_profit[idx] = max_steps + 1;
    }
}
""")

def get_output_prices(tradeup):
    outputs_details = tradeup.get('outputs_details', {})
    return [details[1] for details in outputs_details.values()]

simulate_profitability = mod.get_function("simulate_profitability")

def simulate_profitability_for_entry(output_prices_list, total_input_cost, num_runs, max_steps, entry_id):
    output_prices = np.array(output_prices_list, dtype=np.float32)
    d_output_prices = cuda.mem_alloc(output_prices.nbytes)
    cuda.memcpy_htod(d_output_prices, output_prices)

    num_steps_to_profit = np.zeros(num_runs, dtype=np.int32)
    d_num_steps_to_profit = cuda.mem_alloc(num_steps_to_profit.nbytes)

    block_size = 512
    grid_size = (num_runs + block_size - 1) // block_size

    simulate_profitability(
        d_output_prices, np.int32(len(output_prices_list)), np.float32(total_input_cost),
        np.int32(num_runs), np.int32(max_steps), np.float32(profit_threshold),
        d_num_steps_to_profit,
        block=(block_size, 1, 1), grid=(grid_size, 1)
    )

    cuda.memcpy_dtoh(num_steps_to_profit, d_num_steps_to_profit)
    
    valid_steps = num_steps_to_profit[num_steps_to_profit <= max_steps]
    if len(valid_steps) == 0:
        print(f"No valid steps for entry ID {entry_id}. Setting num_steps_needed to {max_steps + 1}.")
        return max_steps + 1

    mean_steps = np.mean(valid_steps)
    if np.isnan(mean_steps):
        print(f"Encountered NaN for entry ID {entry_id} with total_input_cost {total_input_cost} and output_prices_list {output_prices_list}. Setting num_steps_needed to {max_steps + 1}.")
        return max_steps + 1

    return mean_steps

# Process each entry in the data with a progress bar
for entry_id, entry in enumerate(tqdm(data, desc="Processing entries")):
    output_prices_list = get_output_prices(entry)
    total_input_cost = entry['Total Input Cost']
    num_steps_needed = simulate_profitability_for_entry(output_prices_list, total_input_cost, num_runs, max_steps, entry_id)
    simulation_cost = num_steps_needed * total_input_cost
    entry['num_steps_needed'] = float(num_steps_needed)
    entry['simulation_cost'] = float(simulation_cost)

# Sort the data based on the total simulation cost
data.sort(key=lambda x: x['simulation_cost'])

def custom_json_dump(obj, file):
    # Convert the object to a JSON string
    json_str = json.dumps(obj, ensure_ascii=False)
    json_str = re.sub(r'â™¥', '♥', json_str)
    file.write(json_str + '\n')

with open('profitable_tradeups_processed.jsonl', 'w', encoding='utf-8') as jsonl_file:
    for entry in data:
        custom_json_dump(entry, jsonl_file)

print("processed JSONL file created as 'profitable_tradeups_processed.jsonl'")
