# 🐜 ACO Route Optimizer – Flask Web App

Aplicación web desarrollada en **Flask (Python)** que determina la **ruta óptima entre múltiples puntos geográficos** a partir de datos extraídos de un archivo **Excel (latitud y longitud)**.  
El sistema está diseñado para optimizar **rutas de distribución** dentro del estado de **Querétaro**, aplicando un algoritmo **bioinspirado (Ant Colony Optimization, ACO)**.

---

## 🚗 **Descripción general**

La aplicación simula el comportamiento de **conductores-vehículos (hormigas)** que colaboran para encontrar las rutas más eficientes entre puntos de entrega.  
Cada vehículo posee características configurables como:

- 🚘 **Capacidad de carga**
- 🧠 **Nivel de experiencia del conductor**
- ⏱️ **Ventanas de tiempo de servicio**

Estos parámetros permiten que el sistema adapte las decisiones del algoritmo a distintos escenarios logísticos.

---

## 🗺️ **Zonas geográficas**

El proyecto opera sobre **7 zonas de Querétaro**, cada una con un número distinto de puntos de destino:

| Zona | Color    | Puntos |
| ---- | -------- | ------ |
| 🟨   | Amarillo | 10     |
| 🟫   | Café     | 21     |
| ⬜   | Gris     | 16     |
| 🔴   | Rojo     | 11     |
| 🌸   | Rosa     | 17     |
| 🟩   | Verde    | 16     |
| 🔵   | Azul     | 15     |

El **punto de partida “Zona Origen”** actúa como base inicial para el cálculo de las rutas.

---

## ⚙️ **Algoritmo ACO**

El motor de decisión utiliza un enfoque **heurístico** inspirado en el comportamiento colectivo de las hormigas.  
Este algoritmo evalúa múltiples variables en cada iteración, incluyendo:

- **Feromonas (α – alpha):** Influencia del rastro dejado por rutas previas.
- **Distancia heurística (β – beta):** Importancia de la proximidad entre nodos.
- **Evaporación (ρ – rho):** Tasa de disminución de feromonas a lo largo del tiempo.
- **Número de iteraciones:** Cantidad de repeticiones del proceso de búsqueda.

> Este método permite generar **rutas adaptativas y eficientes**, incluso en entornos con múltiples restricciones y combinaciones posibles.

---

## 💻 **Interfaz web**

Desarrollada en **Flask + HTML + JavaScript + CSS moderno**, con un diseño responsive.
La interfaz permite:

- Ingresar o cargar parámetros del algoritmo (α, β, ρ, iteraciones).
- Agregar o eliminar vehículos dinámicamente.
- Definir experiencia y capacidad de cada vehículo.
- Visualizar resultados en un **mapa geográfico interactivo (GeoPandas / Folium)**.
- Obtener el **orden óptimo de visita** de cada vehículo.
