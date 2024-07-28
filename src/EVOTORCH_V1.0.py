import torch
import json
import random
from tqdm import tqdm
from evotorch import Problem, SolutionBatch
from evotorch.algorithms import GeneticAlgorithm
from evotorch.operators import CrossOver, Operator
from functools import partial
import logging
import argparse
from line_profiler import LineProfiler

profiler = LineProfiler()



@profiler
def check_unique_values(tensor):
    
    # Convert tensor to a list of values
    values = tensor.tolist()
    
    # Dictionary to track indices of each value
    value_indices = {}
    
    # Iterate over the specified range (TOTAL_NUM_ITEMS to TOTAL_NUM_ITEMS-1) to populate the dictionary
    for idx in range(TOTAL_NUM_ITEMS, TOTAL_NUM_ITEMS-1):
        value = values[idx]
        if value in value_indices:
            value_indices[value].append(idx)
        else:
            value_indices[value] = [idx]
    
    # Check for repeated values and print their indices
    repeated_values = {value: indices for value, indices in value_indices.items() if len(indices) > 1}
    
    if repeated_values:
        #print("The following values are repeated (within indices TOTAL_NUM_ITEMS to TOTAL_NUM_ITEMS-1):")
        for value, indices in repeated_values.items():
            #print(f"Value {value} repeats at indices: {indices}")
            pass
        return repeated_values

    return None

# Configure logging
logging.getLogger("evotorch").setLevel(logging.WARNING)

# Load JSON data
with open('processed_items.json', 'r') as file:
    processed_items = json.load(file)

# Define factory function for generating individuals
@profiler
def generate_individual(tradeup_data):
    cases = tradeup_data[0]['cases']

    case_items = {case: [] for case in cases}

    # Populate the case_items dictionary with items from each case
    for case, items in tradeup_data[1].items():
        if case in case_items:
            case_items[case].extend(items)

    # Get the first and second cases for base and modifier collections
    case_keys = list(cases.keys())
    base_case = case_keys[0]
    modifier_case = case_keys[1]

    base_collection_count = cases[base_case] * NUM_TRADEUPS
    modifier_collection_count = cases[modifier_case] * NUM_TRADEUPS

    if len(case_items[base_case]) < base_collection_count:
        raise ValueError(f"Not enough unique items in {base_case} to meet the requirement of {base_collection_count}.")
    if len(case_items[modifier_case]) < modifier_collection_count:
        raise ValueError(f"Not enough unique items in {modifier_case} to meet the requirement of {modifier_collection_count}.")

    # Sample items for the base and modifier collections
    base_collection = random.sample(case_items[base_case], base_collection_count)
    modifier_collection = random.sample(case_items[modifier_case], modifier_collection_count)

    selected_items = base_collection + modifier_collection

    return selected_items



class CustomMutation(Operator):
    @profiler
    def __init__(self, problem, mutation_rate, tradeup_data):
        super().__init__(problem)
        self.mutation_rate = mutation_rate
        self.tradeup_data = tradeup_data

        self.cases = tradeup_data[0]['cases']
        self.NUM_TRADEUPS = NUM_TRADEUPS
        self.case_items = {case: [] for case in self.cases}

        for case, items in tradeup_data[1].items():
            if case in self.case_items:
                self.case_items[case].extend(items)

        case_keys = list(self.cases.keys())
        self.base_case = case_keys[0]
        self.modifier_case = case_keys[1]

        self.base_collection_count = self.cases[self.base_case] * self.NUM_TRADEUPS
        self.modifier_collection_count = self.cases[self.modifier_case] * self.NUM_TRADEUPS

    @profiler
    def _do(self, solutions: SolutionBatch):
        sln_values = solutions.access_values()
        for i in range(len(sln_values)):
            sln_values[i] = self._mutate_individual(sln_values[i])

    @profiler
    def _mutate_individual(self, individual):
        mutated = individual.clone()
        num_items = len(individual) // 2

        # Create sets for current values
        current_price_set = set(mutated[j].item() for j in range(num_items))
        current_float_set = set(mutated[j + num_items].item() for j in range(num_items))

        # Determine number of items to replace
        base_num_to_replace = int(self.base_collection_count * self.mutation_rate)
        modifier_num_to_replace = int(self.modifier_collection_count * self.mutation_rate)

        if base_num_to_replace > 0:
            self._replace_items(mutated, num_items, base_num_to_replace, self.base_case, current_price_set, current_float_set, range(self.base_collection_count))
        
        if modifier_num_to_replace > 0:
            self._replace_items(mutated, num_items, modifier_num_to_replace, self.modifier_case, current_price_set, current_float_set, range(self.base_collection_count, self.base_collection_count + self.modifier_collection_count))

        self._check_and_replace_repeated_values(mutated, current_price_set, current_float_set)

        return mutated

    @profiler
    def _replace_items(self, mutated, num_items, num_to_replace, case, current_price_set, current_float_set, positions):
        new_items = self._generate_unique_items(num_to_replace, current_price_set, current_float_set, case)
        positions_to_replace = random.sample(positions, num_to_replace)
        
        for idx, pos in enumerate(positions_to_replace):
            mutated[pos] = new_items[idx]['price']
            mutated[pos + num_items] = new_items[idx]['floatvalue']

    @profiler
    def _check_and_replace_repeated_values(self, mutated, current_price_set, current_float_set):
        repeated_values = check_unique_values(mutated)
        if repeated_values:
            for value, indices in repeated_values.items():
                for index in indices:
                    case = self.base_case if index < self.base_collection_count else self.modifier_case
                    replacement_item = self._generate_unique_items(1, current_price_set, current_float_set, case)[0]
                    
                    mutated[index - TOTAL_NUM_ITEMS] = replacement_item['price']
                    mutated[index] = replacement_item['floatvalue']
                    
                    current_price_set.add(replacement_item['price'])
                    current_float_set.add(replacement_item['floatvalue'])

    @profiler
    def _generate_unique_items(self, num_items, current_price_set, current_float_set, case):
        available_items = [item for item in self.case_items[case] if item['floatvalue'] not in current_float_set]
        available_items_set = set(item['floatvalue'] for item in available_items)

        if len(available_items) < num_items:
            raise ValueError(f"Not enough unique items available for mutation in case {case}.")

        unique_items = []
        while len(unique_items) < num_items:
            item = random.choice(available_items)
            if item['floatvalue'] not in current_float_set:
                unique_items.append(item)
                current_float_set.add(item['floatvalue'])
                available_items.remove(item)

        return unique_items




class CustomCrossOver(CrossOver):
    @profiler
    def __init__(self, problem, tradeup_data, tournament_size=2, cross_over_rate=0.7):
        super().__init__(problem, tournament_size=tournament_size)
        self.cross_over_rate = cross_over_rate
        self.cases = tradeup_data[0]['cases']
        self.NUM_TRADEUPS = NUM_TRADEUPS
        self.base_case = list(self.cases.keys())[0]
        self.modifier_case = list(self.cases.keys())[1]
        self.base_collection_count = self.cases[self.base_case] * self.NUM_TRADEUPS
        self.modifier_collection_count = self.cases[self.modifier_case] * self.NUM_TRADEUPS

    @profiler
    def _do_cross_over(self, parents1: torch.Tensor, parents2: torch.Tensor) -> SolutionBatch:
        assert len(parents1) == len(parents2)

        childpop = SolutionBatch(self.problem, popsize=2*NUM_PARENTS, empty=True)
        childpop_values = childpop.access_values()

        for i in range(NUM_PARENTS):
            #if random.random() < self.cross_over_rate: shelved
                # Get unique items from base collections
            base_items1 = set((parents1[i][j].item(), parents1[i][j + TOTAL_NUM_ITEMS].item()) for j in range(self.base_collection_count))
            base_items2 = set((parents2[i][j].item(), parents2[i][j + TOTAL_NUM_ITEMS].item()) for j in range(self.base_collection_count))
            unique_base_items = list(base_items1.union(base_items2))

            if len(unique_base_items) > self.base_collection_count*1.25:

                base_child1_items = unique_base_items[:self.base_collection_count]
                base_child2_items = unique_base_items[-self.base_collection_count:]

                # Get unique items from modifier collections
                modifier_items1 = set((parents1[i][j].item(), parents1[i][j + TOTAL_NUM_ITEMS].item()) for j in range(TOTAL_NUM_ITEMS - self.modifier_collection_count, TOTAL_NUM_ITEMS))
                modifier_items2 = set((parents2[i][j].item(), parents2[i][j + TOTAL_NUM_ITEMS].item()) for j in range(TOTAL_NUM_ITEMS - self.modifier_collection_count, TOTAL_NUM_ITEMS))
                unique_modifier_items = list(modifier_items1.union(modifier_items2))

                if len(unique_modifier_items) < self.modifier_collection_count:
                    raise ValueError("Not enough unique items to create a crossover child from modifier collection.")

                modifier_child1_items = unique_modifier_items[:self.modifier_collection_count]
                modifier_child2_items = unique_modifier_items[-self.modifier_collection_count:]

                # Combine base and modifier items
                child1_items = base_child1_items + modifier_child1_items
                child2_items = base_child2_items + modifier_child2_items

                # Create child tensors
                child1 = self._create_child_tensor(child1_items)
                child2 = self._create_child_tensor(child2_items)

                childpop_values[i*2] = child1
                childpop_values[i*2 + 1] = child2
                global crossover_success
                crossover_success+=1
            else:
                childpop_values[i*2] = parents1[i]
                childpop_values[i*2 + 1] = parents2[i]
                global crossover_failure
                crossover_failure+=1

        return childpop

    @profiler
    def _create_child_tensor(self, items):
        child = torch.zeros(2*TOTAL_NUM_ITEMS, dtype=self.problem.dtype, device=self.problem.device)
        
        # Populate the child tensor
        for i, (price, float_value) in enumerate(items):
            if i >= TOTAL_NUM_ITEMS:
                break
            child[i] = price
            child[i + TOTAL_NUM_ITEMS] = float_value

        return child


# Define fitness function
@profiler
def evaluate(individual, avg_float, tradeup_price):
    num_items = len(individual) // 2
    prices = individual[:num_items]
    float_values = individual[num_items:]
    
    total_price = sum(prices)
    total_float = sum(float_values)
    avg_float_value = total_float / num_items
    
    price_deviation = total_price / TOTAL_NUM_ITEMS - tradeup_price
    float_deviation = avg_float_value - avg_float

    # Penalty factors
    float_penalty_factor = 1000
    price_penalty_factor = 100
    
    fitness = 0
    if price_deviation <= 0:
        fitness += 20
    else:
        fitness -= price_deviation * price_penalty_factor
    
    if float_deviation <= 0:
        fitness += 50
    else:
        fitness -= float_deviation * float_penalty_factor
    #print(f'\n Fitness: {fitness}')
    return fitness

# Define a function to flatten a population
@profiler
def flatten_population(population):
    flattened = []
    for individual in population:
        num_items = len(individual)
        flattened.extend([item['price'] for item in individual] + [item['floatvalue'] for item in individual])

    return flattened

# Define a custom problem class
class CustomProblem(Problem):
    @profiler
    def __init__(self, eval_func, solution_length, dtype, device, tradeup_data, avg_float, tradeup_price):
        super().__init__(
            objective_func=eval_func,
            objective_sense="max",
            solution_length=solution_length,
            dtype=dtype,
            device=device,
        )
        self.tradeup_data = tradeup_data
        self.avg_float = avg_float
        self.tradeup_price = tradeup_price
    
    @profiler
    def _fill(self, values: torch.Tensor):
        num_solutions = values.size(0)
        solution_length = values.size(1)
        
        # Generate initial population
        initial_population = [generate_individual(self.tradeup_data) for _ in range(num_solutions)]
        
        for i, individual in enumerate(initial_population):
            if len(individual) == 0:
                continue
            num_items = len(individual)

            prices = [item['price'] for item in individual]
            float_values = [item['floatvalue'] for item in individual]
            values[i, :num_items] = torch.tensor(prices, dtype=self.dtype, device=self.device)
            values[i, num_items:num_items*2] = torch.tensor(float_values, dtype=self.dtype, device=self.device)
    
    @profiler
    def _evaluate_batch(self, solutions):
        for i, solution in enumerate(solutions):
            individual = solution.values.cpu().numpy()
            fitness = evaluate(individual, self.avg_float, self.tradeup_price)
            solution.set_evals(fitness)
    

@profiler
def main(start_index, end_index):
    with open('processed_items.json', 'r') as file:
        processed_items = json.load(file)

    tradeup_items = list(processed_items.items())[start_index:end_index]
    
    output_filename = f'best_individuals_{start_index}_to_{end_index}.txt'

    for i, (tradeup_key, tradeup_data) in enumerate(tqdm(tradeup_items, desc=f'Processing Tradeups {start_index}-{end_index}')):
        params = tradeup_data[0]
        avg_float = params['avg_float']
        tradeup_price = params['tradeup_price']

        eval_func = partial(evaluate, avg_float=avg_float, tradeup_price=tradeup_price)

        solution_length = len(flatten_population([generate_individual(tradeup_data)]))
        problem = CustomProblem(
            eval_func=eval_func,
            solution_length=solution_length,
            dtype=torch.float32,
            device = "cpu",
            tradeup_data=tradeup_data,
            avg_float=avg_float,
            tradeup_price=tradeup_price,      
        )

        ga = GeneticAlgorithm(
            problem,
            popsize=POP_SIZE,
            operators=[
                CustomCrossOver(problem, tournament_size=2, cross_over_rate=0.85, tradeup_data=tradeup_data),
                CustomMutation(problem, mutation_rate=0.2, tradeup_data=tradeup_data),
            ],
            elitist=True
        )       


        with tqdm(total=NGENS, desc=f'Evolution Generation {i+start_index}', leave=False) as pbar:
            for _ in range(NGENS):
                ga.step()
                pbar.update(1)

        # Get all individuals
        all_individuals = ga.population.values.cpu().tolist()

        valid_individuals = []

        for individual in all_individuals:
            num_items = len(individual) // 2
            prices = individual[:num_items]
            float_values = individual[num_items:]
            
            total_price = sum(prices)
            total_float = sum(float_values)
            avg_float_value = total_float / num_items

            price_deviation = total_price / num_items - tradeup_price
            float_deviation = avg_float_value - avg_float

            if price_deviation <= 0 and float_deviation <= 0:
                valid_individuals.append((individual, price_deviation, float_deviation))

        # Write results to the range-specific file
        with open(output_filename, 'a') as file:
            if valid_individuals:
                for valid_individual, price_dev, float_dev in valid_individuals:
                    file.write(f"Best Tradeup: {tradeup_key}\n")
                    file.write(f"Best Individual: {valid_individual}\n")
                    file.write(f"price_deviation: {price_dev:.4f}\n")
                    file.write(f"float_deviation: {float_dev:.4f}\n")
                    file.write("------\n")
            else:
                best_individual = all_individuals[0]
                num_items = len(best_individual) // 2
                prices = best_individual[:num_items]
                float_values = best_individual[num_items:]
                
                total_price = sum(prices)
                total_float = sum(float_values)
                avg_float_value = total_float / num_items
                
                price_deviation = total_price / num_items - tradeup_price
                float_deviation = avg_float_value - avg_float

                file.write(f"Best Tradeup: {tradeup_key}\n")
                file.write(f"Best Individual: {best_individual}\n")
                file.write(f"price_deviation: {price_deviation:.4f}\n")
                file.write(f"float_deviation: {float_deviation:.4f}\n")
                file.write("------\n")

        if valid_individuals:
            print(f"\nValid individuals found for {tradeup_key}: {len(valid_individuals)}")
            print('Valid individuals:\n')
            for x in valid_individuals:
                print(x)
            print('\n')

    print('after running:')
    print(f'crossover_success: {crossover_success}, crossover_failure: {crossover_failure}')
    print(f'crossover success rate: {(crossover_success/(crossover_success+crossover_failure))*100}%')


if __name__ == "__main__":

    crossover_success=0
    crossover_failure=0

    NGENS = 400
    NUM_TRADEUPS= 1
    TOTAL_NUM_ITEMS = 10*NUM_TRADEUPS
    POP_SIZE = 200
    NUM_PARENTS = POP_SIZE//2

    parser = argparse.ArgumentParser(description='Process a range of tradeups.')
    parser.add_argument('start', type=int, help='Start index of tradeups to process')
    parser.add_argument('end', type=int, help='End index of tradeups to process')
    args = parser.parse_args()


    main(args.start,args.end)

    #profiler.print_stats()
