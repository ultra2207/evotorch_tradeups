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

# Configure logging
logging.getLogger("evotorch").setLevel(logging.WARNING)

# Load JSON data
with open('processed_items.json', 'r') as file:
    processed_items = json.load(file)

# Define factory function for generating individuals
def generate_individual(tradeup_data):
    cases = tradeup_data[0]['cases']
    selected_items = []

    all_items = []
    for case, items in tradeup_data[1].items():
        all_items.extend(items)

    if len(all_items) < 10:
        raise ValueError(f"Not enough unique items to create an individual.")

    selected_items = random.sample(all_items, 10)
    print(selected_items)
    # Check for 0.0 values and replace them
    for i in range(len(selected_items)):
        if selected_items[i]['price'] == 0.0 or selected_items[i]['floatvalue'] == 0.0:
            print(f"Detected 0.0 value in generate_individual at index {i}, replacing...")
            new_item = random.choice([item for item in all_items if item not in selected_items])
            selected_items[i] = new_item

    return selected_items

class CustomMutation(Operator):
    def __init__(self, problem, mutation_rate, tradeup_data):
        super().__init__(problem)
        self.mutation_rate = mutation_rate
        self.tradeup_data = tradeup_data
        self.all_items = []
        for case, items in tradeup_data[1].items():
            self.all_items.extend(items)

    def _do(self, solutions: SolutionBatch):
        sln_values = solutions.access_values()
        
        for i in range(len(sln_values)):
            mutated_individual = self._mutate_individual(sln_values[i])
            sln_values[i] = mutated_individual

    def _mutate_individual(self, individual):
        mutated = individual.clone()
        num_items = len(individual) // 2

        current_pairs = [(mutated[j].item(), mutated[j + num_items].item()) for j in range(num_items)]

        for j in range(num_items):
            if random.random() < self.mutation_rate:
                new_item = self._generate_random_item(current_pairs)
                mutated[j] = new_item['price']
                mutated[j + num_items] = new_item['floatvalue']
                current_pairs[j] = (new_item['price'], new_item['floatvalue'])

        # Check for 0.0 values and replace them
        for j in range(num_items):
            if mutated[j] == 0.0 or mutated[j + num_items] == 0.0:

                #Not printing this as this behaviour of index 9 being 0 is expected and dealt with properly, no changes necessary
                #print(f"Detected 0.0 value in CustomMutation at index {j}, replacing...")  Not printing
                new_item = self._generate_random_item(current_pairs)
                mutated[j] = new_item['price']
                mutated[j + num_items] = new_item['floatvalue']
                current_pairs[j] = (new_item['price'], new_item['floatvalue'])

        return mutated

    def _generate_random_item(self, current_pairs):
        available_items = [item for item in self.all_items if (item['price'], item['floatvalue']) not in current_pairs]
        if not available_items:
            raise ValueError("No unique items available for mutation.")
        return random.choice(available_items)

class CustomCrossOver(CrossOver):
    def __init__(self, problem, tournament_size=2, cross_over_rate=0.7):
        super().__init__(problem, tournament_size=tournament_size)
        self.cross_over_rate = cross_over_rate

    def _do_cross_over(
        self,
        parents1: torch.Tensor,
        parents2: torch.Tensor,
    ) -> SolutionBatch:
        assert len(parents1) == len(parents2)
        num_parents = len(parents1)

        childpop = SolutionBatch(self.problem, popsize=num_parents*2, empty=True)
        childpop_values = childpop.access_values()

        for i in range(num_parents):
            if random.random() < self.cross_over_rate:
                crossover_point1 = random.randint(1, 9)
                crossover_point2 = 9 - crossover_point1  # Opposite point

                child1 = self._create_child(parents1[i], parents2[i], crossover_point1)
                child2 = self._create_child(parents1[i], parents2[i], crossover_point2)

                childpop_values[i*2] = child1
                childpop_values[i*2+1] = child2
            else:
                childpop_values[i*2] = parents1[i]
                childpop_values[i*2+1] = parents2[i]

        return childpop

    def _create_child(self, parent1, parent2, crossover_point):
        child = torch.zeros_like(parent1)
        
        # Extract item pairs from parents
        items1 = [(parent1[i].item(), parent1[i+10].item()) for i in range(10)]
        items2 = [(parent2[i].item(), parent2[i+10].item()) for i in range(10)]

        # Check for 0.0 values in parents
        for i in range(10):
            if items1[i][0] == 0.0 or items1[i][1] == 0.0 or items2[i][0] == 0.0 or items2[i][1] == 0.0:
                print(f"Detected 0.0 value in CustomCrossOver at index {i}, replacing...")
                items1[i] = random.choice([item for item in items1 if item not in items2])
                items2[i] = random.choice([item for item in items2 if item not in items1])

        # Create child items
        child_items = items1[:crossover_point] + items2[crossover_point:]
        
        # Ensure we have 10 unique pairs
        unique_pairs = list(dict.fromkeys(child_items))
          # Preserve order, remove duplicates
        if len(unique_pairs) < 10:
            # If we don't have 10 unique pairs, fill with unique pairs from the other parent
            remaining_items = [item for item in items2 if item not in unique_pairs]
            unique_pairs.extend(remaining_items[:10 - len(unique_pairs)])

        # Ensure we have exactly 10 pairs
        child_items = unique_pairs[:10]

        # Shuffle the child items
        random.shuffle(child_items)

        # Populate the child tensor
        for i, (price, float_value) in enumerate(child_items):
            child[i] = price
            child[i+10] = float_value

        return child

# Define fitness function
def evaluate(individual, avg_float, tradeup_price):
    num_items = len(individual) // 2
    prices = individual[:num_items]
    float_values = individual[num_items:]
    
    total_price = sum(prices)
    total_float = sum(float_values)
    avg_float_value = total_float / num_items
    
    price_deviation = total_price / 10 - tradeup_price
    float_deviation = avg_float_value - avg_float

    # Penalty factors
    float_penalty_factor = 1000
    price_penalty_factor = 1
    
    fitness = 0
    if price_deviation <= 0:
        fitness += 10
    else:
        fitness -= price_deviation * price_penalty_factor
    
    if float_deviation <= 0:
        fitness += 50
    else:
        fitness -= float_deviation * float_penalty_factor
    #print(f'\n Fitness: {fitness}')
    return fitness

# Define a function to flatten a population
def flatten_population(population):
    flattened = []
    for individual in population:
        num_items = len(individual)
        flattened.extend([item['price'] for item in individual] + [item['floatvalue'] for item in individual])
    return flattened

# Define a custom problem class
class CustomProblem(Problem):
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
    
    def _evaluate_batch(self, solutions):
        for i, solution in enumerate(solutions):
            individual = solution.values.cpu().numpy()
            fitness = evaluate(individual, self.avg_float, self.tradeup_price)
            solution.set_evals(fitness)
    

def main(start_index, end_index):
    with open('processed_items.json', 'r') as file:
        processed_items = json.load(file)

    tradeup_items = list(processed_items.items())[start_index:end_index]
    
    # Create a unique filename for this range of tradeups
    output_filename = f'best_individuals_{start_index}_to_{end_index}.txt'

    for i, (tradeup_key, tradeup_data) in enumerate(tqdm(tradeup_items, desc=f'Processing Tradeups {start_index}-{end_index}')):
        params = tradeup_data[0]
        avg_float = params['avg_float']
        tradeup_price = params['tradeup_price']
        params = tradeup_data[0]
        avg_float = params['avg_float']
        tradeup_price = params['tradeup_price']

        eval_func = partial(evaluate, avg_float=avg_float, tradeup_price=tradeup_price)

        solution_length = len(flatten_population([generate_individual(tradeup_data)]))
        problem = CustomProblem(
            eval_func=eval_func,
            solution_length=solution_length,
            dtype=torch.float32,
            device="cuda:0" if torch.cuda.is_available() else "cpu",
            tradeup_data=tradeup_data,
            avg_float=avg_float,
            tradeup_price=tradeup_price,      
        )

        ga = GeneticAlgorithm(
            problem,
            popsize=200,
            operators=[
                CustomCrossOver(problem, tournament_size=2, cross_over_rate=0.85),
                CustomMutation(problem, mutation_rate=0.2, tradeup_data=tradeup_data),
            ],
            elitist=True
        )       
    
        NGENS = 100

        with tqdm(total=NGENS, desc=f'Running Evolution {i}', leave=False) as pbar:
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

        # Modified part to write results to the range-specific file
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


if __name__ == "__main__":
    '''
    parser = argparse.ArgumentParser(description='Process a range of tradeups.')
    parser.add_argument('start', type=int, help='Start index of tradeups to process')
    parser.add_argument('end', type=int, help='End index of tradeups to process')
    args = parser.parse_args()
    '''

    main(0,99)