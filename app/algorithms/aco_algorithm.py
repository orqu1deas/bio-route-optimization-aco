import os
import math
import random
import numpy as np
import pandas as pd
from distance import build_distance_matrix

# 1. Cargar y construimos la matriz de distancias
ruta_excel = "app/data/data.xlsx"

dist_df = build_distance_matrix(ruta_excel, method = "auto")

distance_matrix = dist_df.to_numpy()
np.fill_diagonal(distance_matrix, np.inf)

# 2. Inicialización ACO
n = len(distance_matrix)
feromone_matrix = np.ones((n, n))
alpha, beta, rho = 1, 2, 0.5

def probabs(current, visited):
    probs = []
    for j in range(n):
        if j not in visited:
            tau = feromone_matrix[current, j] ** alpha
            eta = (1 / distance_matrix[current, j]) ** beta
            probs.append(tau * eta)
        else:
            probs.append(0)
    probs = np.array(probs)
    probs = probs / probs.sum()
    return probs

def select_next_city(current, visited):
    probs = probabs(current, visited)
    return np.random.choice(range(n), p = probs)

def build_route(start=0):
    route = [start]
    while len(route) < n:
        next_city = select_next_city(route[-1], route)
        route.append(next_city)
    return route

def route_length(route):
    length = 0
    for i in range(len(route) - 1):
        length += distance_matrix[route[i], route[i + 1]]
    return length

def update_pheromones(routes):
    global feromone_matrix
    # Evaporación
    feromone_matrix *= (1 - rho)
    for r in routes:
        L = route_length(r)
        for i in range(len(r) - 1):
            a, b = r[i], r[i + 1]
            feromone_matrix[a, b] += 1 / L

def aco_algorithm(iterations = 10, num_ants = 3):
    best_solution = {"Distance": float("inf"), "Route": []}

    for iteration in range(1, iterations + 1):
        print(f"\n===== ITERATION {iteration} =====")
        ants = [build_route() for _ in range(num_ants)]

        for idx, route in enumerate(ants, 1):
            distance = route_length(route)
            print(f"Ant {idx}: {route}, Distance = {distance:.2f}")

            if distance < best_solution["Distance"]:
                best_solution["Distance"] = distance
                best_solution["Route"] = route

        update_pheromones(ants)

    print("\nFinal pheromone matrix:\n", np.round(feromone_matrix, 3))
    print(f"\nBest route found: {best_solution['Route']} "
          f"with total distance = {best_solution['Distance']:.2f} km")

    return best_solution
