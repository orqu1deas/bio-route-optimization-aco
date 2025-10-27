from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import geopandas as gpd
import folium
import numpy as np
import os
import io
from algorithms.aco_algorithm import aco_algorithm

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/edit')
def edit_page():
    return render_template('edit.html')

@app.route('/genetic')
def genetic_page():
    return render_template('genetic.html')

@app.route('/aco')
def aco_page():
    return render_template('aco.html')


@app.route('/run_aco', methods=['POST'])
def run_aco():
    try:
        data = request.get_json()

        alpha = float(data.get('alpha', 1))
        beta = float(data.get('beta', 2))
        rho = float(data.get('rho', 0.5))
        iterations = int(data.get('iterations', 5))

        vehicles_info = data.get('vehicles', [])
        vehicles = {}
        vehicle_experience = {}

        for v in vehicles_info:
            name = v['name']
            vehicles[name] = {'capacity': float(v['capacity'])}
            vehicle_experience[name] = float(v['experience'])

        # 1️. Leer matriz de distancias
        dist_path = os.path.join('app', 'data', 'distances.csv')
        dist_df = pd.read_csv(dist_path, index_col=0)
        distance_matrix = dist_df.to_numpy(dtype=float)
        np.fill_diagonal(distance_matrix, np.inf)
        demands = [10] * len(distance_matrix)

        # 2️. Ejecutar algoritmo
        best_solution = aco_algorithm(
            distance_matrix=distance_matrix,
            vehicles=vehicles,
            demands=demands,
            vehicle_experience=vehicle_experience,
            iterations=iterations,
            alpha=alpha,
            beta=beta,
            rho=rho,
            num_ants=3
        )

        # 3️. Cargar coordenadas
        coords_path = os.path.join('app', 'data', 'data.xlsx')
        coords_df = pd.read_excel(coords_path)
        coords_df.columns = coords_df.columns.str.lower().str.strip()
        lat_col = next((c for c in coords_df.columns if "lat" in c), None)
        lon_col = next((c for c in coords_df.columns if "lon" in c), None)

        gdf = gpd.GeoDataFrame(
            coords_df,
            geometry=gpd.points_from_xy(coords_df[lon_col], coords_df[lat_col])
        )

        # 4️. Crear mapa Folium
        start_point = gdf.iloc[0].geometry
        m = folium.Map(location=[start_point.y, start_point.x], zoom_start=13)
        colors = ['red', 'blue', 'green', 'purple', 'orange']

        route_summary = []
        for i, (car, route) in enumerate(best_solution['Route'].items()):
            if not route:
                continue
            points = [gdf.iloc[int(r)].geometry for r in route if int(r) < len(gdf)]
            coords = [(p.y, p.x) for p in points]

            folium.PolyLine(coords, color=colors[i % len(colors)], weight=4, tooltip=car).add_to(m)

            order_text = []
            for j, r in enumerate(route):
                if int(r) >= len(gdf): continue
                row = gdf.iloc[int(r)]
                name = row.get('nombre', f"Punto {r}")
                folium.CircleMarker(location=[row.geometry.y, row.geometry.x],
                                    radius=5, color=colors[i % len(colors)],
                                    fill=True, tooltip=f"{car}: {name}").add_to(m)
                order_text.append(f"{j+1}. {name}")
            route_summary.append({
                'vehicle': car,
                'route': route,
                'order': "\n".join(order_text)
            })

        map_html = m._repr_html_()

        # 5. Convertir np.int64 → int (para JSON)
        def convert_to_serializable(obj):
            if isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(x) for x in obj]
            elif isinstance(obj, np.integer):
                return int(obj)
            else:
                return obj

        best_solution_serializable = convert_to_serializable(best_solution)
        route_summary_serializable = convert_to_serializable(route_summary)
        visited_indices = set()
        for r in best_solution_serializable['Route'].values():
            visited_indices.update(int(i) for i in r if isinstance(i, (int, np.integer)))
        
        all_indices = set(range(len(dist_df)))
        missing_sites = all_indices - visited_indices
        if 'nombre' in coords_df.columns:
            missing_sites_list = [
                coords_df.iloc[i]['nombre'] for i in missing_sites if i < len(coords_df)
                ]
        else:
            name_col = next((c for c in coords_df.columns if 'direccion' in c or 'address' in c), None)
            if name_col:
                missing_sites_list = [
                    coords_df.iloc[i][name_col] for i in missing_sites if i < len(coords_df)
                ]
            else:
                missing_sites_list = [f"Punto {i}" for i in missing_sites]

        # 6. Responder con resultados
        return jsonify({
            'best_distance': round(best_solution_serializable['Distance'], 2),
            'map_html': map_html,
            'routes': route_summary_serializable,
            'missing_sites': missing_sites_list
        })

    except Exception as e:
        return jsonify({'error': str(e)})


if __name__ == '__main__':
    app.run(debug=True)
