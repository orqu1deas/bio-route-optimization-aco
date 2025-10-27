# app/algorithms/genetic_algorithm.py
import os
import random
import numpy as np
import pandas as pd

dist_path = os.path.join('app', 'data', 'data.xlsx')
datosCargados = pd.read_excel(dist_path)
print(datosCargados.head())




almacen = datosCargados[datosCargados['Zona'] == 'Zona Origen']
datos = datosCargados

xAl = almacen.iloc[0, 2]
yAl = almacen.iloc[0, 3]
print(xAl, yAl)

origen = datos[datos['Zona'] == 'Zona Origen']
zonaR = datos[datos['Zona'] == 'Zona Roja']
zonaRo = datos[datos['Zona'] == 'Zona Rosa']
zonaC = datos[datos['Zona'] == 'Zona Cafe']
zonaA = datos[datos['Zona'] == 'Zona Amarillo']
zonaG = datos[datos['Zona'] == 'Zona Gris']
zonaB = datos[datos['Zona'] == 'Zona azul']
zonaV = datos[datos['Zona'] == 'Zona Verde']

#hacer la matriz de la distancia ulizando la distancia euclidiana
distancias = np.zeros((len(datos), len(datos)))
for i in range(len(datos)):
  for j in range(len(datos)):
    distancias[i, j] = np.sqrt((datos.iloc[i, 2] - datos.iloc[j, 2])**2 + (datos.iloc[i, 3] - datos.iloc[j, 3])**2)
print(distancias)

#demandas por cliente
demandas = datosCargados["Demanda"]
#capacidad del vehículo
capacidad = 500 #kg

#Parámetros del algoritmo
pop_size = 100
generations = 300
prob_cruce = 0.9
prob_mutacion = 0.2
penalizacion = 10000


# ₊˚ ‿︵‿︵‿︵୨୧ · · ♡ · · ୨୧‿︵‿︵‿︵ ˚₊
#           1. Inicialización GA
# ₊˚ ‿︵‿︵‿︵୨୧ · · ♡ · · ୨୧‿︵‿︵‿︵ ˚₊

#peso del tiempo
def vel_prom(hora):
    if 7 <= hora < 9:
        return 20
    elif 9 <= hora < 14:
        return 30
    elif 14 <= hora < 19:
        return 15
    else:
        return 40

def fitness(individuo, distancias, demandas, capacidad, penalizacion, hora_inicio=8):
    rutas = []
    carga_actual = 0
    ruta_actual = []

    for cliente in individuo:
        demanda = demandas[cliente]
        if carga_actual + demanda > capacidad:
            rutas.append(ruta_actual)
            ruta_actual = [cliente]
            carga_actual = demanda
        else:
            ruta_actual.append(cliente)
            carga_actual += demanda
    rutas.append(ruta_actual)

    total = 0
    tiempo_total = 0
    vel = vel_prom(hora_inicio)

    for ruta in rutas:
        carga = sum(demandas[i] for i in ruta)
        if carga > capacidad:
            total += penalizacion * (carga - capacidad)

        nodoAnterior = 0  # depósito
        for cliente in ruta:
            d = distancias[nodoAnterior, cliente]
            total += d
            tiempo_total += d / vel
            nodoAnterior = cliente
        d = distancias[nodoAnterior, 0]
        total += d
        tiempo_total += d / vel

    return total, tiempo_total

def mutacion(individuo, prob):
    mutado = individuo.copy()
    if random.random() < prob:
        i, j = random.sample(range(len(mutado)), 2)
        mutado[i], mutado[j] = mutado[j], mutado[i]
    return mutado

def crossover(ind1, ind2):
    n = len(ind1)
    p1, p2 = sorted(random.sample(range(n), 2))
    hijo = [None] * n
    hijo[p1:p2] = ind1[p1:p2]

    pos = p2
    for c in ind2:
        if c not in hijo:
            if pos == n:
                pos = 0
            hijo[pos] = c
            pos += 1
    return hijo

def GA(distancias, demandas, capacidad,
       pop_size, generations, prob_cruce, prob_mutacion, penalizacion):

    clientes = demandas.index.to_list()
    poblacion = [random.sample(clientes, len(clientes)) for _ in range(pop_size)]
    num_elite = int(0.2 * pop_size)

    for _ in range(generations):
        costos = []
        for ind in poblacion:
            costo, tiempo = fitness(ind, distancias, demandas, capacidad, penalizacion)
            costos.append((costo, tiempo, ind))

        costos.sort(key=lambda x: x[0])

#elitismo
        nueva_poblacion = [ind for (_, _, ind) in costos[:num_elite]]

        while len(nueva_poblacion) < pop_size:
            p1, p2 = random.sample(costos[:num_elite], 2)
            if random.random() < prob_cruce:
                hijo = crossover(p1[2], p2[2])
            else:
                hijo = p1[2].copy()
            hijo = mutacion(hijo, prob_mutacion)
            nueva_poblacion.append(hijo)

        poblacion = nueva_poblacion

    mejor_costo, mejor_tiempo, mejor_individuo = sorted(costos, key=lambda x: x[0])[0]
    
    return mejor_individuo, mejor_costo, mejor_tiempo

mejor_individuo, mejor_costo, mejor_tiempo = GA(
    distancias, demandas, capacidad, pop_size, generations,
    prob_cruce, prob_mutacion, penalizacion
)

print("Mejor ruta:", mejor_individuo)
print(f"Distancia: {mejor_costo:.2f}")
print(f"Tiempo en horas{mejor_tiempo:.2f}")