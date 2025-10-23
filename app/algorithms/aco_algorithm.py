import os
import math
import random
import numpy as np
import pandas as pd
from distance import build_distance_matrix

# ₊˚ ‿︵‿︵‿︵୨୧ · · ♡ · · ୨୧‿︵‿︵‿︵ ˚₊
# 1. Carga y construcción de la matriz de distancias
# ₊˚ ‿︵‿︵‿︵୨୧ · · ♡ · · ୨୧‿︵‿︵‿︵ ˚₊
ruta_excel = "app/data/data.xlsx"

construction = False

if construction == True:
    dist_df = build_distance_matrix(ruta_excel, method = "auto")
    distance_matrix = dist_df.to_numpy(dtype=float)
else:
    dist_df = pd.read_csv("app/data/distances.csv", index_col=0)
    distance_matrix = dist_df.to_numpy(dtype=float)

np.fill_diagonal(distance_matrix, np.inf)


# ₊˚ ‿︵‿︵‿︵୨୧ · · ♡ · · ୨୧‿︵‿︵‿︵ ˚₊
#           2. Inicialización ACO
# ₊˚ ‿︵‿︵‿︵୨୧ · · ♡ · · ୨୧‿︵‿︵‿︵ ˚₊

# Información Básica
n = len(distance_matrix)
feromone_matrix = np.ones((n, n))

alpha, beta, rho = 1, 2, 0.5

vehicles = {
    "Car_1": {"capacity": 1000, "load": 0, "route": []},
    "Car_2": {"capacity": 1000,  "load": 0, "route": []},
}

demands = [10] * n


# Algoritmo
def probabs(current, unvisited):
    probs = []
    for j in range(n):
        if j in unvisited:
            tau = feromone_matrix[current, j] ** alpha
            eta = (1 / distance_matrix[current, j]) ** beta
            probs.append(tau * eta)
        else:
            probs.append(0)
    probs = np.array(probs)
    probs = probs / probs.sum()
    return probs

def select_next_city(current, unvisited):
    probs = probabs(current, unvisited)
    return np.random.choice(range(n), p = probs)

def build_route_for_vehicles(vehicles, demands):
    unvisited = set(range(len(distance_matrix)))
    unvisited.remove(0)
    routes = {v : [] for v in vehicles.keys()}

    for car_name, car in vehicles.items():
        current_capacity = 0
        current_city = 0
        while unvisited:
            feasible = [j for j in unvisited if current_capacity + demands[j] <= car["capacity"]]

            if not feasible:
                break

            next_city = select_next_city(current_city, unvisited)
            
            routes[car_name].append(next_city)
            current_capacity += demands[next_city]
            unvisited.remove(next_city)
            current_city = next_city

    return routes

def total_distance(vehicle_routes):
    total = 0
    for route in vehicle_routes.values():
        for i in range(len(route) - 1):
            total += distance_matrix[route[i], route[i +1 ]]
    return total

def update_pheromones(vehicle_routes):
    global feromone_matrix
    # Evaporación
    feromone_matrix *= (1 - rho)
    
    for routes in vehicle_routes:
        print(routes)
        L = total_distance(routes)
        for car, route in routes.items():
            for i in range(len(route) - 1):
                a, b = route[i], route[i + 1]
                feromone_matrix[a, b] += 1 / L
                feromone_matrix[b, a] += 1 / L

def aco_algorithm(iterations = 10, num_ants = 3):
    best_solution = {"Distance": float("inf"), "Route": []}

    for iteration in range(1, iterations + 1):
        print(f"\n===== ITERATION {iteration} =====")
        ants = [build_route_for_vehicles(vehicles, demands) for _ in range(num_ants)]
        print(ants)
        for idx, routes in enumerate(ants, 1):
            distance = total_distance(routes)
            print(f"Ant {idx}, Total Distance = {distance:2f}")
            for car_name, route in routes.items():
                print(f"          {car_name}: {route}")

            if distance < best_solution["Distance"]:
                best_solution["Distance"] = distance
                best_solution["Route"] = route

        update_pheromones(ants)

        print(f"Best distance so far: {best_solution['Distance']:.2f}")

    print("\nFinal pheromone matrix:\n", np.round(feromone_matrix, 3))
    print(f"\nBest route found: \n{best_solution['Route']}")
    print(f"Total distance = {best_solution['Distance']:.2f} km")

    return best_solution

if __name__ == "__main__":
    aco_algorithm()