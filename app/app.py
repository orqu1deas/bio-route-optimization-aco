from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import geopandas as gpd, folium
import numpy as np
import os
import io
from algorithms.aco_algorithm import aco_algorithm
from algorithms.genetic_algorithm import GA_multi_vehicle

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/edit")
def edit_page():
    return render_template("edit.html")

@app.route('/genetic')
def genetic_page():
    return render_template('genetic.html')

@app.route('/aco')
def aco_page():
    return render_template('aco.html')

@app.route("/save_selection", methods=["POST"])
def save_selection():
    try:
        data = request.get_json()
        selected_zones = data.get("zones", [])
        selected_stores = data.get("stores", [])

        coords_path = os.path.join("app", "data", "data.xlsx")
        df = pd.read_excel(coords_path)
        df.columns = df.columns.str.strip()

        df["Zona"] = df["Zona"].astype(str).str.strip().str.lower()
        df["Nombre"] = df["Nombre"].astype(str).str.strip().str.lower()
        selected_zones_norm = [z.lower() for z in selected_zones]
        selected_stores_norm = [s.lower() for s in selected_stores]

        zone_map = {
            "amarillo": "zona amarilla",
            "café": "zona cafe",
            "cafe": "zona cafe",
            "gris": "zona gris",
            "rojo": "zona roja",
            "rosa": "zona rosa",
            "verde": "zona verde",
            "azul": "zona azul",
        }
        mapped_zones = [zone_map.get(z, z) for z in selected_zones_norm]

        filtered_df = df[df["Zona"].isin(mapped_zones)]
        if selected_stores_norm:
            filtered_df = pd.concat(
                [filtered_df, df[df["Nombre"].isin(selected_stores_norm)]]
            ).drop_duplicates()

        origin_row = df[df["Zona"].str.contains("origen", case=False)]
        if not origin_row.empty:
            filtered_df = pd.concat([origin_row, filtered_df]).drop_duplicates()

        if filtered_df.empty:
            return jsonify({"error": f"No se encontraron puntos válidos para {selected_zones}."})

        dist_path = os.path.join("app", "data", "total_distances.csv")
        dist_df = pd.read_csv(dist_path, index_col=0)
        dist_df.index = dist_df.index.astype(str)
        dist_df.columns = dist_df.columns.astype(str)

        origin_idx = origin_row.index.tolist()
        other_idx = [i for i in filtered_df.index if i not in origin_idx]
        selected_indices = origin_idx + other_idx

        filtered_matrix = dist_df.iloc[selected_indices, selected_indices]
        filtered_df = df.loc[selected_indices]

        out_path = os.path.join("app", "data", "distances.csv")
        filtered_matrix.reset_index(drop=True).to_csv(out_path, index=True)

        coords_df = filtered_df.copy()
        coords_df.columns = coords_df.columns.str.lower()
        lat_col = next((c for c in coords_df.columns if "lat" in c), None)
        lon_col = next((c for c in coords_df.columns if "lon" in c), None)

        gdf = gpd.GeoDataFrame(
            coords_df,
            geometry=gpd.points_from_xy(coords_df[lon_col], coords_df[lat_col]),
        )

        start = gdf.iloc[0].geometry
        m = folium.Map(location=[start.y, start.x], zoom_start=12)

        color_map = {
            "zona amarilla": "yellow",
            "zona cafe": "brown",
            "zona gris": "gray",
            "zona roja": "red",
            "zona rosa": "pink",
            "zona verde": "green",
            "zona azul": "blue",
            "zona origen": "black",
        }

        for _, row in gdf.iterrows():
            folium.CircleMarker(
                location=[row.geometry.y, row.geometry.x],
                radius=6,
                color=color_map.get(row["zona"], "black"),
                fill=True,
                fill_color=color_map.get(row["zona"], "black"),
                fill_opacity=0.8,
                tooltip=row.get("nombre", row["zona"]),
            ).add_to(m)

        map_html = m._repr_html_()

        return jsonify({
            "message": "Selección guardada correctamente.",
            "count": len(filtered_df),
            "map_html": map_html
        })

    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/run_ga', methods=['POST'])
def run_ga():
    try:
        data = request.get_json()

        pop_size = int(data.get('pop_size', 80))
        generations = int(data.get('generations', 300))
        prob_crossover = float(data.get('prob_crossover', 0.9))
        prob_mutation = float(data.get('prob_mutation', 0.2))
        vehicles_info = data.get('vehicles', [])

        vehicles = {v['name']: {'capacity': float(v['capacity'])} for v in vehicles_info}

        dist_path = os.path.join('app', 'data', 'distances.csv')
        dist_df = pd.read_csv(dist_path, index_col=0)
        distance_matrix = dist_df.to_numpy(dtype=float)
        np.fill_diagonal(distance_matrix, np.inf)

        selected_idx = dist_df.index.astype(int).tolist()

        data_path = os.path.join('app', 'data', 'data.xlsx')
        df_all = pd.read_excel(data_path)
        
        df_aligned = df_all.loc[selected_idx].reset_index(drop=True)

        demands = df_aligned['Demanda'].to_numpy()

        best_solution = GA_multi_vehicle(
            distance_matrix=distance_matrix,
            demands=demands,
            vehicles=vehicles,
            pop_size=pop_size,
            generations=generations,
            prob_crossover=prob_crossover,
            prob_mutation=prob_mutation,
            penalty=10000
        )

        coords_df = df_aligned.copy()
        coords_df.columns = coords_df.columns.str.lower().str.strip()
        lat_col = next((c for c in coords_df.columns if "lat" in c), None)
        lon_col = next((c for c in coords_df.columns if "lon" in c), None)

        gdf = gpd.GeoDataFrame(
            coords_df,
            geometry=gpd.points_from_xy(coords_df[lon_col], coords_df[lat_col])
        )

        start_point = gdf.iloc[0].geometry
        m = folium.Map(location=[start_point.y, start_point.x], zoom_start=13)
        colors = ["purple", "orange", "teal", "blue", "red"]

        route_summary = []
        for i, (car, route) in enumerate(best_solution["Routes"].items()):
            if not route:
                continue
            color = colors[i % len(colors)]
            coords = [
                (gdf.iloc[int(r)].geometry.y, gdf.iloc[int(r)].geometry.x)
                for r in route if int(r) < len(gdf)
            ]
            folium.PolyLine(coords, color=color, weight=5, tooltip=car).add_to(m)
            order_text = []
            for j, r in enumerate(route):
                if int(r) >= len(gdf): continue
                name = gdf.iloc[int(r)].get("nombre", f"Punto {r}")
                folium.CircleMarker(
                    location=[gdf.iloc[int(r)].geometry.y, gdf.iloc[int(r)].geometry.x],
                    radius=5, color=color, fill=True,
                    tooltip=f"{car}: {name}"
                ).add_to(m)
                order_text.append(f"{j+1}. {name}")
            route_summary.append({"vehicle": car, "order": "\n".join(order_text)})

        map_html = m._repr_html_()

        return jsonify({
            "best_cost": round(best_solution["Cost"], 2),
            "best_time": round(best_solution["Time"], 2),
            "routes": route_summary,
            "map_html": map_html
        })

    except Exception as e:
        return jsonify({'error': str(e)})

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

        dist_path = os.path.join('app', 'data', 'distances.csv')
        dist_df = pd.read_csv(dist_path, index_col=0)
        distance_matrix = dist_df.to_numpy(dtype=float)
        np.fill_diagonal(distance_matrix, np.inf)
        demands = [10] * len(distance_matrix)

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

        coords_path = os.path.join('app', 'data', 'data.xlsx')
        coords_df = pd.read_excel(coords_path)
        coords_df.columns = coords_df.columns.str.lower().str.strip()
        lat_col = next((c for c in coords_df.columns if "lat" in c), None)
        lon_col = next((c for c in coords_df.columns if "lon" in c), None)

        gdf = gpd.GeoDataFrame(
            coords_df,
            geometry=gpd.points_from_xy(coords_df[lon_col], coords_df[lat_col])
        )

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
