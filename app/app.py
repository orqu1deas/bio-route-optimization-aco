from flask import Flask, render_template, request, jsonify
from algorithms.aco_algorithm import aco_algorithm
import pandas as pd

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/run", methods=["POST"])
def run_algorithm():
    # 1. Leer parámetros del formulario
    num_ants = int(request.form.get("num_ants", 3))
    iterations = int(request.form.get("iterations", 10))
    num_vehicles = int(request.form.get("num_vehicles", 2))
    capacity = int(request.form.get("capacity", 1000))

    # 2. Construir diccionario dinámico de vehículos
    vehicles = {f"Car_{i+1}": {"capacity": capacity, "load": 0, "route": []}
                for i in range(num_vehicles)}

    # 3. Cargar matriz desde CSV
    dist_df = pd.read_csv("app/data/distances.csv", index_col=0)
    distance_matrix = dist_df.to_numpy(dtype=float)

    # 4. Ejecutar ACO
    best_solution = aco_algorithm()

    # 5. Devolver JSON a la vista
    return jsonify(best_solution)

