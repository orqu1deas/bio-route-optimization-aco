import os
from flask import Flask, render_template, request, jsonify
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, LineString
import folium
from folium import plugins
import json
import numpy as np

app = Flask(__name__)

# Simulación del modelo de predicción (tu equipo de IA lo reemplazará)
class ModeloPrediccionRutas:
    """
    Esta clase simula el modelo de predicción que será desarrollado por el equipo de IA.
    El equipo deberá implementar los métodos:
    - entrenar() si es necesario
    - predecir_ruta() que retorna la ruta óptima
    """
    
    def __init__(self):
        self.modelo_entrenado = True  # Simula que el modelo está listo
        
    def predecir_ruta(self, grafo, origen, destino, coche_id):
        """
        MÉTODO A IMPLEMENTAR POR EL EQUIPO DE IA
        
        Args:
            grafo: dict con estructura {nodo: {vecino: peso}}
            origen: nodo de inicio
            destino: nodo de destino
            coche_id: identificador del coche
            
        Returns:
            list: secuencia de nodos que forman la ruta óptima
        """
        # IMPLEMENTACIÓN TEMPORAL - Dijkstra simple (reemplazar con modelo de IA)
        return self._dijkstra_simple(grafo, origen, destino)
    
    def _dijkstra_simple(self, grafo, origen, destino):
        """Implementación básica de Dijkstra - SOLO PARA DEMOSTRACIÓN"""
        distancias = {nodo: float('inf') for nodo in grafo}
        distancias[origen] = 0
        visitados = set()
        padres = {origen: None}
        
        while len(visitados) < len(grafo):
            nodo_actual = None
            min_distancia = float('inf')
            
            for nodo in grafo:
                if nodo not in visitados and distancias[nodo] < min_distancia:
                    min_distancia = distancias[nodo]
                    nodo_actual = nodo
            
            if nodo_actual is None or nodo_actual == destino:
                break
                
            visitados.add(nodo_actual)
            
            for vecino, peso in grafo[nodo_actual].items():
                distancia = distancias[nodo_actual] + peso
                if distancia < distancias[vecino]:
                    distancias[vecino] = distancia
                    padres[vecino] = nodo_actual
        
        # Reconstruir ruta
        ruta = []
        nodo = destino
        while nodo is not None:
            ruta.append(nodo)
            nodo = padres.get(nodo)
        
        return list(reversed(ruta))

# Instancia del modelo
modelo_prediccion = ModeloPrediccionRutas()

class GestorGrafo:
    """Maneja la estructura del grafo y las coordenadas"""
    
    def __init__(self):
        self.nodos = {}  # {nodo_id: {'lat': lat, 'lon': lon}}
        self.aristas = {}  # {nodo_id: {vecino_id: peso}}
        
    def agregar_nodo(self, nodo_id, lat, lon):
        self.nodos[nodo_id] = {'lat': lat, 'lon': lon}
        if nodo_id not in self.aristas:
            self.aristas[nodo_id] = {}
    
    def agregar_arista(self, origen, destino, peso):
        if origen not in self.aristas:
            self.aristas[origen] = {}
        self.aristas[origen][destino] = peso
    
    def crear_geodataframe_nodos(self):
        """Crea GeoDataFrame de nodos"""
        if not self.nodos:
            return None
        
        datos = []
        for nodo_id, coords in self.nodos.items():
            datos.append({
                'nodo_id': nodo_id,
                'geometry': Point(coords['lon'], coords['lat'])
            })
        
        return gpd.GeoDataFrame(datos, crs='EPSG:4326')
    
    def crear_geodataframe_aristas(self):
        """Crea GeoDataFrame de aristas"""
        if not self.aristas:
            return None
        
        datos = []
        for origen, vecinos in self.aristas.items():
            for destino, peso in vecinos.items():
                if origen in self.nodos and destino in self.nodos:
                    origen_coords = self.nodos[origen]
                    destino_coords = self.nodos[destino]
                    
                    datos.append({
                        'origen': origen,
                        'destino': destino,
                        'peso': peso,
                        'geometry': LineString([
                            (origen_coords['lon'], origen_coords['lat']),
                            (destino_coords['lon'], destino_coords['lat'])
                        ])
                    })
        
        return gpd.GeoDataFrame(datos, crs='EPSG:4326')

gestor_grafo = GestorGrafo()

def crear_mapa_interactivo(rutas_coches=None):
    """Crea un mapa de Folium con el grafo y las rutas"""
    
    # Obtener GeoDataFrames
    gdf_nodos = gestor_grafo.crear_geodataframe_nodos()
    gdf_aristas = gestor_grafo.crear_geodataframe_aristas()
    
    if gdf_nodos is None or len(gdf_nodos) == 0:
        # Mapa por defecto en Querétaro
        return folium.Map(location=[20.5888, -100.3899], zoom_start=13)
    
    # Calcular centro del mapa
    centro_lat = gdf_nodos.geometry.y.mean()
    centro_lon = gdf_nodos.geometry.x.mean()
    
    # Crear mapa base
    mapa = folium.Map(
        location=[centro_lat, centro_lon],
        zoom_start=13,
        tiles='OpenStreetMap'
    )
    
    # Agregar aristas (carreteras)
    if gdf_aristas is not None:
        for _, arista in gdf_aristas.iterrows():
            coords = [(lat, lon) for lon, lat in arista.geometry.coords]
            folium.PolyLine(
                coords,
                color='gray',
                weight=2,
                opacity=0.4,
                popup=f"Peso: {arista['peso']:.2f}"
            ).add_to(mapa)
    
    # Agregar nodos
    for _, nodo in gdf_nodos.iterrows():
        folium.CircleMarker(
            location=[nodo.geometry.y, nodo.geometry.x],
            radius=5,
            color='blue',
            fill=True,
            popup=f"Nodo: {nodo['nodo_id']}",
            fillOpacity=0.7
        ).add_to(mapa)
    
    # Agregar rutas de los coches
    if rutas_coches:
        colores = ['red', 'green', 'purple', 'orange', 'darkblue', 'pink']
        
        for i, (coche_id, info_ruta) in enumerate(rutas_coches.items()):
            ruta = info_ruta['ruta']
            costo = info_ruta['costo']
            color = colores[i % len(colores)]
            
            # Crear línea de ruta
            coords_ruta = []
            for nodo_id in ruta:
                if nodo_id in gestor_grafo.nodos:
                    nodo = gestor_grafo.nodos[nodo_id]
                    coords_ruta.append((nodo['lat'], nodo['lon']))
            
            if len(coords_ruta) > 1:
                folium.PolyLine(
                    coords_ruta,
                    color=color,
                    weight=4,
                    opacity=0.8,
                    popup=f"Coche {coche_id}<br>Costo: {costo:.2f}"
                ).add_to(mapa)
                
                # Marcar inicio y fin
                folium.Marker(
                    coords_ruta[0],
                    popup=f"Inicio Coche {coche_id}",
                    icon=folium.Icon(color=color.replace('dark', ''), icon='play', prefix='fa')
                ).add_to(mapa)
                
                folium.Marker(
                    coords_ruta[-1],
                    popup=f"Destino Coche {coche_id}",
                    icon=folium.Icon(color=color.replace('dark', ''), icon='flag-checkered', prefix='fa')
                ).add_to(mapa)
    
    return mapa

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cargar_grafo', methods=['POST'])
def cargar_grafo():
    """Endpoint para cargar nodos y aristas"""
    try:
        datos = request.json
        
        # Limpiar grafo anterior
        gestor_grafo.nodos.clear()
        gestor_grafo.aristas.clear()
        
        # Cargar nodos
        for nodo in datos.get('nodos', []):
            gestor_grafo.agregar_nodo(
                nodo['id'],
                nodo['lat'],
                nodo['lon']
            )
        
        # Cargar aristas
        for arista in datos.get('aristas', []):
            gestor_grafo.agregar_arista(
                arista['origen'],
                arista['destino'],
                arista['peso']
            )
        
        return jsonify({
            'success': True,
            'nodos_cargados': len(gestor_grafo.nodos),
            'aristas_cargadas': sum(len(v) for v in gestor_grafo.aristas.values())
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/calcular_rutas', methods=['POST'])
def calcular_rutas():
    """Endpoint para calcular rutas óptimas usando el modelo de IA"""
    try:
        datos = request.json
        coches = datos.get('coches', [])
        
        rutas_calculadas = {}
        
        # Calcular ruta para cada coche usando el modelo de IA
        for coche in coches:
            coche_id = coche['id']
            origen = coche['origen']
            destino = coche['destino']
            
            # AQUÍ SE USA EL MODELO DE IA
            ruta = modelo_prediccion.predecir_ruta(
                gestor_grafo.aristas,
                origen,
                destino,
                coche_id
            )
            
            # Calcular costo total
            costo_total = 0
            for i in range(len(ruta) - 1):
                nodo_actual = ruta[i]
                nodo_siguiente = ruta[i + 1]
                if nodo_siguiente in gestor_grafo.aristas.get(nodo_actual, {}):
                    costo_total += gestor_grafo.aristas[nodo_actual][nodo_siguiente]
            
            rutas_calculadas[coche_id] = {
                'ruta': ruta,
                'costo': costo_total
            }
        
        # Crear mapa con las rutas
        mapa = crear_mapa_interactivo(rutas_calculadas)
        mapa_html = mapa._repr_html_()
        
        return jsonify({
            'success': True,
            'rutas': rutas_calculadas,
            'mapa_html': mapa_html
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/visualizar_grafo', methods=['GET'])
def visualizar_grafo():
    """Endpoint para visualizar el grafo sin rutas"""
    try:
        mapa = crear_mapa_interactivo()
        mapa_html = mapa._repr_html_()
        
        return jsonify({
            'success': True,
            'mapa_html': mapa_html
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

if __name__ == '__main__':
    # Crear carpeta de templates si no existe
    os.makedirs('templates', exist_ok=True)
    
    # Crear archivo HTML
    html_content = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema de Ruteo Inteligente</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .content {
            display: grid;
            grid-template-columns: 400px 1fr;
            gap: 0;
            min-height: 600px;
        }
        
        .sidebar {
            background: #f8f9fa;
            padding: 30px;
            border-right: 2px solid #e0e0e0;
            overflow-y: auto;
        }
        
        .map-container {
            padding: 20px;
            background: #fff;
        }
        
        #map {
            width: 100%;
            height: 600px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .section {
            margin-bottom: 30px;
        }
        
        .section h3 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        
        textarea {
            width: 100%;
            min-height: 150px;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            resize: vertical;
        }
        
        textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            font-weight: 600;
            width: 100%;
            margin-top: 10px;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        .btn:active {
            transform: translateY(0);
        }
        
        .btn-secondary {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        
        .alert {
            padding: 12px;
            border-radius: 8px;
            margin-top: 15px;
            display: none;
        }
        
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .coche-input {
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            border: 2px solid #e0e0e0;
        }
        
        .coche-input input {
            width: 100%;
            padding: 8px;
            margin: 5px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        
        .coche-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .remove-btn {
            background: #dc3545;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.8em;
        }
        
        #resultados {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
            max-height: 200px;
            overflow-y: auto;
        }
        
        .ruta-info {
            background: white;
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            border-left: 4px solid #667eea;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚗 Sistema de Ruteo Inteligente</h1>
            <p>Optimización de rutas con IA y GeoPandas</p>
        </div>
        
        <div class="content">
            <div class="sidebar">
                <div class="section">
                    <h3>📍 Cargar Grafo</h3>
                    <p style="font-size: 0.9em; color: #666; margin-bottom: 10px;">
                        Formato JSON: nodos (id, lat, lon) y aristas (origen, destino, peso)
                    </p>
                    <textarea id="grafoInput" placeholder='{
  "nodos": [
    {"id": "A", "lat": 20.5888, "lon": -100.3899},
    {"id": "B", "lat": 20.5950, "lon": -100.3850}
  ],
  "aristas": [
    {"origen": "A", "destino": "B", "peso": 5.2}
  ]
}'></textarea>
                    <button class="btn" onclick="cargarGrafo()">Cargar Grafo</button>
                    <button class="btn btn-secondary" onclick="visualizarGrafo()">Visualizar Grafo</button>
                    <div id="alertGrafo" class="alert"></div>
                </div>
                
                <div class="section">
                    <h3>🚕 Configurar Coches</h3>
                    <div id="cochesContainer"></div>
                    <button class="btn btn-secondary" onclick="agregarCoche()">+ Agregar Coche</button>
                    <button class="btn" onclick="calcularRutas()">Calcular Rutas Óptimas</button>
                    <div id="alertRutas" class="alert"></div>
                </div>
                
                <div id="resultados"></div>
            </div>
            
            <div class="map-container">
                <div id="map"></div>
            </div>
        </div>
    </div>
    
    <script>
        let cocheCount = 0;
        
        function agregarCoche() {
            cocheCount++;
            const container = document.getElementById('cochesContainer');
            const cocheDiv = document.createElement('div');
            cocheDiv.className = 'coche-input';
            cocheDiv.id = `coche-${cocheCount}`;
            cocheDiv.innerHTML = `
                <div class="coche-header">
                    <strong>Coche ${cocheCount}</strong>
                    <button class="remove-btn" onclick="removerCoche(${cocheCount})">Eliminar</button>
                </div>
                <input type="text" placeholder="ID del coche" id="id-${cocheCount}" value="coche_${cocheCount}">
                <input type="text" placeholder="Nodo origen (ej: A)" id="origen-${cocheCount}">
                <input type="text" placeholder="Nodo destino (ej: B)" id="destino-${cocheCount}">
            `;
            container.appendChild(cocheDiv);
        }
        
        function removerCoche(id) {
            const elemento = document.getElementById(`coche-${id}`);
            if (elemento) {
                elemento.remove();
            }
        }
        
        function showAlert(elementId, message, type) {
            const alert = document.getElementById(elementId);
            alert.className = `alert alert-${type}`;
            alert.textContent = message;
            alert.style.display = 'block';
            setTimeout(() => {
                alert.style.display = 'none';
            }, 5000);
        }
        
        async function cargarGrafo() {
            try {
                const grafoText = document.getElementById('grafoInput').value;
                const grafo = JSON.parse(grafoText);
                
                const response = await fetch('/cargar_grafo', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(grafo)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showAlert('alertGrafo', 
                        `✓ Grafo cargado: ${data.nodos_cargados} nodos, ${data.aristas_cargadas} aristas`, 
                        'success');
                } else {
                    showAlert('alertGrafo', `✗ Error: ${data.error}`, 'error');
                }
            } catch (error) {
                showAlert('alertGrafo', `✗ Error: ${error.message}`, 'error');
            }
        }
        
        async function visualizarGrafo() {
            try {
                const response = await fetch('/visualizar_grafo');
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('map').innerHTML = data.mapa_html;
                    showAlert('alertGrafo', '✓ Grafo visualizado', 'success');
                } else {
                    showAlert('alertGrafo', `✗ Error: ${data.error}`, 'error');
                }
            } catch (error) {
                showAlert('alertGrafo', `✗ Error: ${error.message}`, 'error');
            }
        }
        
        async function calcularRutas() {
            try {
                const coches = [];
                const cochesElements = document.querySelectorAll('.coche-input');
                
                cochesElements.forEach(cocheEl => {
                    const id = cocheEl.querySelector('[id^="id-"]').value;
                    const origen = cocheEl.querySelector('[id^="origen-"]').value;
                    const destino = cocheEl.querySelector('[id^="destino-"]').value;
                    
                    if (id && origen && destino) {
                        coches.push({id, origen, destino});
                    }
                });
                
                if (coches.length === 0) {
                    showAlert('alertRutas', '✗ Agrega al menos un coche', 'error');
                    return;
                }
                
                const response = await fetch('/calcular_rutas', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({coches})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('map').innerHTML = data.mapa_html;
                    mostrarResultados(data.rutas);
                    showAlert('alertRutas', '✓ Rutas calculadas exitosamente', 'success');
                } else {
                    showAlert('alertRutas', `✗ Error: ${data.error}`, 'error');
                }
            } catch (error) {
                showAlert('alertRutas', `✗ Error: ${error.message}`, 'error');
            }
        }
        
        function mostrarResultados(rutas) {
            const resultadosDiv = document.getElementById('resultados');
            let html = '<h3 style="color: #667eea; margin-bottom: 10px;">📊 Resultados</h3>';
            
            for (const [cocheId, info] of Object.entries(rutas)) {
                html += `
                    <div class="ruta-info">
                        <strong>${cocheId}</strong><br>
                        Ruta: ${info.ruta.join(' → ')}<br>
                        Costo total: ${info.costo.toFixed(2)}
                    </div>
                `;
            }
            
            resultadosDiv.innerHTML = html;
        }
        
        // Inicializar con un coche por defecto
        agregarCoche();
        
        // Mapa inicial
        document.getElementById('map').innerHTML = '<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #999;"><p>Carga un grafo para visualizar el mapa</p></div>';
    </script>
</body>
</html>'''
    
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("=" * 60)
    print("🚀 SISTEMA DE RUTEO INTELIGENTE")
    print("=" * 60)
    print("\n📝 INSTRUCCIONES PARA EL EQUIPO DE IA:")
    print("\n1. El modelo debe implementarse en la clase 'ModeloPrediccionRutas'")
    print("2. Método principal: predecir_ruta(grafo, origen, destino, coche_id)")
    print("3. Debe retornar una lista de nodos que forman la ruta óptima")
    print("4. Actualmente usa Dijkstra como placeholder - REEMPLAZAR con su modelo")
    print("\n" + "=" * 60)
    print("\n🌐 Servidor iniciando en: http://localhost:5000")
    print("\n" + "=" * 60)
    
    app.run(debug=True, port=5000)