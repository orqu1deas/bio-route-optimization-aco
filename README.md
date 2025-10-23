Aplicación web desarrollada en Flask (Python) que determina la ruta óptima entre múltiples puntos geográficos a partir de datos extraídos de un archivo Excel (latitud y longitud). El sistema opera sobre 7 zonas de Querétaro, cada una con una cantidad específica de destinos:

🟨 Amarillo: 10 puntos
🟫 Café: 21 puntos
⬜ Gris: 16 puntos
🔴 Rojo: 11 puntos
🌸 Rosa: 17 puntos
🟩 Verde: 16 puntos
🔵 Azul: 15 puntos

El punto de partida Zona Origen sirve como origen para calcular la mejor ruta de distribución. El motor de decisión se basa en un algoritmo bioinspirado, que simula comportamientos de conducción y evalúa variables como:

Nivel de experiencia de los conductores
Condiciones de tráfico (con distancia)
Factores de riesgo

Este enfoque heurístico permite generar rutas eficientes y adaptativas, incluso en escenarios complejos.
