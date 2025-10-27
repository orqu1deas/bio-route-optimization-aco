# 🐜 ACO Route Optimizer – Flask Web App

Aplicación web desarrollada en **Flask (Python)** que determina la ruta óptima entre múltiples puntos geográficos a partir de datos extraídos de un archivo Excel (latitud y longitud).
El sistema está diseñado para optimizar rutas de distribución urbana dentro del estado de Querétaro, aplicando dos algoritmos **bioinspirados**: Ant Colony Optimization **(ACO)** y Genetic Algorithm **(GA)**.

---

## 🚗 **Descripción general**

La aplicación busca simular el proceso de **entrega de productos en la última milla**, considerando restricciones reales como:

- 🚘 **Capacidad de carga de los vehículos**
- 🧠 **Nivel de experiencia de los conductores**
- ⏱️ **Ventanas de tiempo para cada punto de entrega**
  Estos parámetros permiten que el sistema adapte dinámicamente la asignación de rutas y decisiones de búsqueda según las condiciones operativas.

---

## 🗺️ Contexto aplicado

El modelo se probó con el caso de Distribuidora Don Pedro, una PyME queretana dedicada a la distribución de productos cárnicos y lácteos.
La empresa cuenta con **dos unidades (500 kg cada una)** y tres rutas principales que cubren zonas como Juriquilla, Milenio, Centro Sur, Felipe Carrillo Puerto y San José el Alto.

Debido a la rotación de personal y limitación de unidades, el sistema busca minimizar la distancia total recorrida y optimizar los tiempos de entrega, integrando así una solución escalable para escenarios con recursos restringidos.

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

**📈 Ventaja:** alta velocidad de convergencia y desempeño estable.
**❗ Restricción:** no permite sobrepasar los límites de tiempo definidos por las ventanas de servicio.

### Genetic Algorithm (GA)

El GA emplea un enfoque evolutivo que combina y muta posibles rutas para mejorar la eficiencia de cada generación. A diferencia del ACO, tolera pequeñas desviaciones en las restricciones de tiempo, lo que lo hace más flexible cuando no hay problema en terminar después del horario límite (p. ej., después de las 17:00).

- Tamaño de población
- Número de generaciones
- Probabilidad de cruce
- Probabilidad de mutación
- Capacidad de cada vehículo (y múltiples vehículos si se usa la versión “multi-vehicle”)

**📈 Ventaja:** permite soluciones más adaptativas cuando se busca equilibrio entre tiempo y costo.
**❗ Restricción:** escenarios donde la puntualidad no sea una restricción rígida, priorizando la optimización global.

---

## 💻 **Interfaz web**

Desarrollada en **Flask + HTML + JavaScript + CSS moderno**, cuenta con una interfaz responsiva y funcional que permite:

- Seleccionar el algoritmo (ACO o GA).
- Configurar parámetros de cada vehículo (capacidad, experiencia, ventana de tiempo).
- Visualizar resultados en un **mapa geográfico interactivo (GeoPandas / Folium)**.
- Obtener el **orden óptimo de visita** de cada vehículo.
