import os
import numpy as np
import pandas as pd
import openrouteservice
from tqdm import tqdm

from haversine import haversine
from geopy.distance import geodesic

USE_ORS = True

try:
    client = openrouteservice.Client(key='eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImUwNWU4Mjc2ZGUwMjQ2MWVhMDk4YzBkNTJmZWY3YjQ1IiwiaCI6Im11cm11cjY0In0=')
except Exception as e:
    print("⚠️ No se pudo inicializar OpenRouteService:", e)
    
USE_ORS = False

def get_distance(coords_i, coords_j, method="auto"):
    """
    Calcula distancia entre coords_i y coords_j.
    Si falla ORS o no hay conexión, usa geodesic o haversine.
    """
    
    if USE_ORS and method in ["auto", "ors"]:
        try:
            route = client.directions([coords_i, coords_j],
                                      profile="driving-car",
                                      format="geojson")
            return route["features"][0]["properties"]["segments"][0]["distance"] / 1000
        except Exception:
            pass
        
    try:
        if method == "haversine":
            return haversine(coords_i[::-1], coords_j[::-1])  # (lat, lon)
        else:
            return geodesic(coords_i[::-1], coords_j[::-1]).km
    except Exception:
        return np.nan



def build_distance_matrix(ruta_excel, method="auto"):
    df = pd.read_excel(ruta_excel)

    origin = df[df["Zona"] == "Blanca"]
    other = df[df["Zona"] != "Blanca"]

    df = pd.concat([origin, other], ignore_index=True)

    coords = list(zip(df["Longitud"], df["Latitud"]))
    n = len(coords)
    matrix = np.zeros((n, n))

    print(f"Calculando distancias ({'ORS' if USE_ORS else 'local'}) para {n} puntos...\n")

    for i in tqdm(range(n)):
        for j in range(n):
            if i == j:
                matrix[i, j] = 0
            else:
                matrix[i, j] = get_distance(coords[i], coords[j], method)

    dist_df = pd.DataFrame(matrix, columns=df["Nombre"], index=df["Nombre"])
    dist_df.to_csv("distances.csv", index=True)
    print("Matriz guardada: distancias_viales.csv")

    return dist_df