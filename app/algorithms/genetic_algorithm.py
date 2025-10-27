# app/algorithms/genetic_algorithm.py
import os
import random
import numpy as np
import pandas as pd


# ₊˚ ‿︵‿︵‿︵୨୧ · · ♡ · · ୨୧‿︵‿︵‿︵ ˚₊
#           1. Inicialización GA
# ₊˚ ‿︵‿︵‿︵୨୧ · · ♡ · · ୨୧‿︵‿︵‿︵ ˚₊

# Peso del time
def average_speed(hour):
    if 7 <= hour < 9:
        return 20
    elif 9 <= hour < 14:
        return 30
    elif 14 <= hour < 19:
        return 15
    else:
        return 40

# Fitness
def fitness(individuo, distance_matrix, demands, capacity, penalty, start_hour=8, service_time=0.15):
    routes = []
    current_load = 0
    current_route = []

    for client in individuo:
        demand = demands[client]
        if current_load + demand > capacity:
            routes.append(current_route)
            current_route = [client]
            current_load = demand
        else:
            current_route.append(client)
            current_load += demand
    routes.append(current_route)

    total = 0
    total_time = 0
    vel = average_speed(start_hour)

    for route in routes:
        load = sum(demands[i] for i in route)
        if load > capacity:
            total += penalty * (load - capacity)

        prev_node = 0  # depósito
        for client in route:
            d = distance_matrix[prev_node, client]
            total += d
            total_time += d / vel + service_time
            prev_node = client
        d = distance_matrix[prev_node, 0]
        total += d
        total_time += d / vel

    return total, total_time

def mutation(individuo, prob):
    mutated = individuo.copy()
    if random.random() < prob:
        i, j = random.sample(range(len(mutated)), 2)
        mutated[i], mutated[j] = mutated[j], mutated[i]
    return mutated

def crossover(ind1, ind2):
    n = len(ind1)
    p1, p2 = sorted(random.sample(range(n), 2))
    child = [None] * n
    child[p1:p2] = ind1[p1:p2]

    pos = p2
    for c in ind2:
        if c not in child:
            if pos == n:
                pos = 0
            child[pos] = c
            pos += 1
    return child

def GA(distance_matrix, demands, capacity=500,
                 pop_size=80, generations=300,
                 prob_crossover=0.9, prob_mutation=0.2, penalty=10000):

    clients = list(range(1, len(demands)))
    population = [random.sample(clients, len(clients)) for _ in range(pop_size)]
    num_elite = int(0.2 * pop_size)
    best_solution = {"Cost": float("inf"), "Route": [], "Time": 0}

    for gen in range(generations):
        costs = []
        for ind in population:
            cost, time = fitness(ind, distance_matrix, demands, capacity, penalty)
            costs.append((cost, time, ind))

        costs.sort(key=lambda x: x[0])
        best_cost, best_time, best_ind = costs[0]

        if best_cost < best_solution["Cost"]:
            best_solution["Cost"] = best_cost
            best_solution["Route"] = best_ind
            best_solution["Time"] = best_time

        # --- Nueva generación (elitismo + cruce + mutación) ---
        new_population = [ind for (_, _, ind) in costs[:num_elite]]

        while len(new_population) < pop_size:
            p1, p2 = random.sample(costs[:num_elite], 2)
            if random.random() < prob_crossover:
                child = crossover(p1[2], p2[2])
            else:
                child = p1[2].copy()
            child = mutation(child, prob_mutation)
            new_population.append(child)

        population = new_population
        print(f"Gen {gen} → Mejor costo: {best_cost:.2f}")

    print("\n=== RESULTADOS FINALES GA ===")
    print(f"Mejor costo total: {best_solution['Cost']:.2f}")
    print(f"Tiempo estimado: {best_solution['Time']:.2f} horas")
    print(f"Ruta óptima: {best_solution['Route']}\n")

    return best_solution

# ₊˚ ‿︵‿︵‿︵୨୧ ✦ FITNESS con más de 1 vehículo ✦ ୨୧‿︵‿︵‿︵ ˚₊
def fitness_multi_vehicle(individuo, distance_matrix, demands, vehicles, penalty, start_hour=8, service_time=0.15):
    vehicle_names = list(vehicles.keys())
    routes = {v: [] for v in vehicle_names}
    current_vehicle = 0
    current_capacity = 0
    current_route = []
    vel = average_speed(start_hour)
    total_cost = 0
    total_time = 0

    for client in individuo:
        demand = demands[client]
        veh_name = vehicle_names[current_vehicle]
        capacity = vehicles[veh_name]['capacity']

        if current_capacity + demand <= capacity:
            current_route.append(client)
            current_capacity += demand
        else:
            routes[veh_name] = current_route.copy()
            current_vehicle += 1
            current_capacity = demand
            current_route = [client]

            if current_vehicle >= len(vehicle_names):
                total_cost += penalty * 100
                break

    if current_vehicle < len(vehicle_names):
        routes[vehicle_names[current_vehicle]] = current_route

    for veh_name, route in routes.items():
        if not route:
            continue
        prev_node = 0
        for client in route:
            d = distance_matrix[prev_node, client]
            total_cost += d
            total_time += d / vel + service_time
            prev_node = client
        d = distance_matrix[prev_node, 0]
        total_cost += d
        total_time += d / vel

    return total_cost, total_time, routes


# ₊˚ ‿︵‿︵‿︵୨୧ ✦ GA con más de un vehículo ✦ ୨୧‿︵‿︵‿︵ ˚₊
def GA_multi_vehicle(distance_matrix, demands, vehicles,
                     pop_size=80, generations=300,
                     prob_crossover=0.9, prob_mutation=0.2, penalty=10000):

    clients = list(range(1, len(demands)))
    population = [random.sample(clients, len(clients)) for _ in range(pop_size)]
    num_elite = int(0.2 * pop_size)
    best_solution = {"Cost": float("inf"), "Routes": {}, "Time": 0}

    for gen in range(generations):
        costs = []
        for ind in population:
            cost, time, routes = fitness_multi_vehicle(ind, distance_matrix, demands, vehicles, penalty)
            costs.append((cost, time, routes, ind))

        costs.sort(key=lambda x: x[0])
        best_cost, best_time, best_routes, best_ind = costs[0]

        if best_cost < best_solution["Cost"]:
            best_solution["Cost"] = best_cost
            best_solution["Routes"] = best_routes
            best_solution["Time"] = best_time

        new_population = [ind for (_, _, _, ind) in costs[:num_elite]]

        while len(new_population) < pop_size:
            p1, p2 = random.sample(costs[:num_elite], 2)
            if random.random() < prob_crossover:
                child = crossover(p1[3], p2[3])
            else:
                child = p1[3].copy()
            child = mutation(child, prob_mutation)
            new_population.append(child)

        population = new_population
        print(f"Gen {gen+1} → Mejor costo: {best_cost:.2f}")

    print("\n=== RESULTADOS GA MULTIVEHÍCULO ===")
    print(f"Mejor costo total: {best_solution['Cost']:.2f}")
    print(f"Tiempo estimado: {best_solution['Time']:.2f} horas")
    print(f"Rutas óptimas: {best_solution['Routes']}")

    return best_solution


# ₊˚ ‿︵‿︵‿︵୨୧ ✦ MAIN TEST ✦ ୨୧‿︵‿︵‿︵ ˚₊
if __name__ == "__main__":
    dist_path = os.path.join("app", "data", "distances.csv")
    dist_df = pd.read_csv(dist_path, index_col = 0)
    distance_matrix = dist_df.to_numpy(dtype=float)
    np.fill_diagonal(distance_matrix, np.inf)

    df_path = os.path.join("app", "data", "data.xlsx")
    df_all = pd.read_excel(df_path)

    selected_idx = dist_df.index.astype(int).tolist()
    df = df_all.loc[selected_idx].reset_index(drop=True)

    demands = df["Demanda"].to_numpy()
    best = GA(distance_matrix, demands, capacity = 500)

    print(best)