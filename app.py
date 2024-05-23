from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2 import sql
import json
import pandas as pd
import re

# Cargar variables de entorno desde .env
load_dotenv()

app = Flask(__name__)

def conectar_a_base_de_datos():
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    return conn

@app.route('/classify', methods=['POST'])
def classify():
    data = request.get_json()
    lat = data.get('lat')
    lon = data.get('lon')

    if lat is None or lon is None:
        return jsonify({"error": "Latitude and longitude are required"}), 400

    try:
        conn = conectar_a_base_de_datos()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT nombre FROM poligonos
        WHERE ST_Intersects(geometria, ST_SetSRID(ST_MakePoint(%s, %s), 4326));
        """, (lon, lat))
        result = cursor.fetchone()
        polygon_name = result[0] if result else "No clasificado"
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({"polygon": polygon_name})

@app.route('/polygon/insert', methods=['POST'])
def insert_polygon():
    data = request.get_json()
    geojson = data.get('geojson')

    if geojson is None:
        return jsonify({"error": "GeoJSON data is required"}), 400

    try:
        geojson_data = json.loads(geojson)
        nombre_del_multi_polygon = geojson_data['features'][0]['properties'].get('name', '')

        if not nombre_del_multi_polygon or not re.match(r"^.+ - \d{7}$", nombre_del_multi_polygon):
            return jsonify({"error": "Invalid polygon name format"}), 400

        polygons = [feature['geometry']['coordinates'] for feature in geojson_data['features']]
        multi_polygon = {"type": "MultiPolygon", "coordinates": polygons}
        multi_polygon_json = json.dumps(multi_polygon)

        conn = conectar_a_base_de_datos()
        cursor = conn.cursor()
        cursor.execute(
            sql.SQL("INSERT INTO poligonos (nombre, geometria) VALUES (%s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326));"),
            (nombre_del_multi_polygon, multi_polygon_json)
        )
        conn.commit()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "Polygon inserted successfully"})

@app.route('/polygon/update', methods=['PUT'])
def update_polygon():
    data = request.get_json()
    old_name = data.get('old_name')
    geojson = data.get('geojson')

    if old_name is None or geojson is None:
        return jsonify({"error": "Old name and GeoJSON data are required"}), 400

    try:
        geojson_data = json.loads(geojson)
        polygons = [feature['geometry']['coordinates'] for feature in geojson_data['features']]
        multi_polygon = {"type": "MultiPolygon", "coordinates": polygons}
        multi_polygon_json = json.dumps(multi_polygon)

        conn = conectar_a_base_de_datos()
        cursor = conn.cursor()
        cursor.execute(
            sql.SQL("UPDATE poligonos SET geometria = ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326) WHERE nombre = %s;"),
            (multi_polygon_json, old_name)
        )
        conn.commit()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "Polygon updated successfully"})

@app.route('/polygon/delete', methods=['DELETE'])
def delete_polygon():
    data = request.get_json()
    name = data.get('name')

    if name is None:
        return jsonify({"error": "Polygon name is required"}), 400

    try:
        conn = conectar_a_base_de_datos()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM poligonos WHERE nombre = %s;", (name,))
        conn.commit()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "Polygon deleted successfully"})

if __name__ == '__main__':
    app.run(debug=True)
