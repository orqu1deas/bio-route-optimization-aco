# app/algorithms/aco_algorithm.py
import os
import math
import random
import numpy as np
import pandas as pd


# ₊˚ ‿︵‿︵‿︵୨୧ · · ♡ · · ୨୧‿︵‿︵‿︵ ˚₊
#           1. Inicialización ACO
# ₊˚ ‿︵‿︵‿︵୨୧ · · ♡ · · ୨୧‿︵‿︵‿︵ ˚₊

# Velocidades estimadas por cada hora
def average_speed(hour):
    if 7 <= hour < 9:
        return 20
    elif 9 <= hour < 14:
        return 30
    elif 14 <= hour < 19:
        return 15
    else:
        return 40

# Algoritmo
def probabs(current, candidates, car_name, distance_matrix, feromone_matrix,
            alpha, beta, vehicle_experience):
    n = len(distance_matrix)
    probs = np.zeros(n, dtype = float)
    exp_level = vehicle_experience[car_name]

    for j in candidates:
        noise = np.random.normal(loc = 0, scale = (1 - exp_level) * 0.15)
        adjusted_dist = distance_matrix[current, j] * (1 + noise)
        
        tau = feromone_matrix[current, j] ** alpha
        eta = (1 / adjusted_dist) ** beta

        probs[j] = tau * eta

    s = probs.sum()
    if s <= 0:
        for j in candidates:
            probs[j] = 1.0
        s = probs.sum()

    return probs / s

def select_next_city(current, candidates, car_name, **kwargs):
    candidates = list(candidates)
    probs = probabs(current, candidates, car_name, **kwargs)
    sub = np.array([probs[j] for j in candidates], dtype = float)
    sub = sub / sub.sum()
    return np.random.choice(candidates, p = sub)

def build_route_for_vehicles(vehicles, demands, distance_matrix, feromone_matrix,
                             alpha, beta, rho, vehicle_experience,
                             open_time, close_time, service_time):
    n = len(distance_matrix)
    unvisited = set(range(n))
    unvisited.remove(0)

    routes = {v : [] for v in vehicles.keys()}

    for car_name, car in vehicles.items():
        current_capacity = 0
        current_city = 0
        current_time = 8.0

        while unvisited:
            feasible = []
            for j in unvisited:
                if current_capacity + demands[j] <= car['capacity']:
                    v = average_speed(current_time)
                    travel_time = distance_matrix[current_city, j] / max(v, 1e-6)
                    arrival_time = current_time + travel_time

                    if arrival_time <= close_time[j]:
                        feasible.append(j)

            if not feasible:
                break

            next_city = select_next_city(
                current_city, feasible, car_name,
                distance_matrix = distance_matrix,
                feromone_matrix = feromone_matrix,
                alpha = alpha, beta = beta,
                vehicle_experience = vehicle_experience
            )

            v = average_speed(current_time)
            travel_time = distance_matrix[current_city, next_city] / max(v, 1e-6)
            arrival_time = current_time + travel_time

            current_time = max(arrival_time, open_time[next_city])
            current_time += service_time[next_city]

            routes[car_name].append(next_city)
            current_capacity += demands[next_city]
            unvisited.remove(next_city)
            current_city = next_city

            if current_time > 15:
                break

    return routes

def total_distance(vehicle_routes, distance_matrix, include_depot = False, depot = 0):
    total = 0
    for route in vehicle_routes.values():
        if not route:
            continue

        if include_depot:
            total += distance_matrix[depot, route[0]]

        for i in range(len(route) - 1):
            total += distance_matrix[route[i], route[i +1 ]]
        
        if include_depot:
            total += distance_matrix[route[-1], depot]
    return total

def update_pheromones(vehicle_routes, feromone_matrix, rho, distance_matrix):
    # Evaporación
    feromone_matrix *= (1 - rho)
    
    for routes in vehicle_routes:
        print(routes)
        L = total_distance(routes, distance_matrix)
        if L <= 1e-9:
            continue
        for car, route in routes.items():
            for i in range(len(route) - 1):
                a, b = route[i], route[i + 1]
                feromone_matrix[a, b] += 1 / L
                feromone_matrix[b, a] += 1 / L

def aco_algorithm(distance_matrix, vehicles, demands,
                  vehicle_experience = None, open_time = None,
                  close_time = None, service_time = None,
                  alpha = 1, beta = 2, rho = 0.5,
                  iterations = 10, num_ants = 3):
    n = len(distance_matrix)
    feromone_matrix = np.ones((n, n))

    if vehicle_experience is None:
        vehicle_experience = {k: 0.8 for k in vehicles.keys()}
    if open_time is None:
        open_time = [7] * n
    if close_time is None:
        close_time = [20] * n
    if service_time is None:
        service_time = [0.15] * n

    best_solution = {"Distance": float("inf"), "Route": {}}

    for iteration in range(1, iterations + 1):
        print(f"\n===== ITERATION {iteration} =====")
        ants = [
            build_route_for_vehicles(
                vehicles, demands, distance_matrix, feromone_matrix,
                alpha, beta, rho, vehicle_experience,
                open_time, close_time, service_time
                )
                for _ in range(num_ants)
        ]

        for idx, routes in enumerate(ants, 1):
            distance = total_distance(routes, distance_matrix)
            print(f"Ant {idx}, Total Distance = {distance:2f}")
            for car_name, route in routes.items():
                print(f"          {car_name}: {route}")

            if distance < best_solution["Distance"]:
                best_solution["Distance"] = distance
                best_solution["Route"] = routes

        update_pheromones(ants, feromone_matrix, rho, distance_matrix)

        print(f"Best distance so far: {best_solution['Distance']:.2f}")

    print("\nFinal pheromone matrix:\n", np.round(feromone_matrix, 3))
    print(f"\nBest route found: \n{best_solution['Route']}")
    print(f"Total distance = {best_solution['Distance']:.2f} km")

    return best_solution


# ₊˚ ‿︵‿︵‿︵୨୧ ✦ MAIN TEST ✦ ୨୧‿︵‿︵‿︵ ˚₊
if __name__ == "__main__":
    dist_df = pd.read_csv("app/data/distances.csv", index_col=0)
    distance_matrix = dist_df.to_numpy(dtype=float)
    np.fill_diagonal(distance_matrix, np.inf)

    vehicles = {
        "Car_1": {"capacity": 1000},
        "Car_2": {"capacity": 800}
    }
    demands = [10] * len(distance_matrix)
    vehicle_experience = {"Car_1": 0.9, "Car_2": 0.6}

    best_solution = aco_algorithm(
        distance_matrix=distance_matrix,
        vehicles=vehicles,
        demands=demands,
        vehicle_experience=vehicle_experience,
        iterations=5,
        num_ants=3
    )

    print("\nTEST COMPLETED")
    print(best_solution)