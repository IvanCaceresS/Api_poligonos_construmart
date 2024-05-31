from flask import Flask, request, jsonify
import pandas as pd
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import os
import json
import re

# Cargar variables de entorno desde .env
load_dotenv('./resources/.env')

app = Flask(__name__)

def conectar_a_base_de_datos():
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")
    return psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)

@app.route('/insert_polygon', methods=['POST'])
def insert_polygon():
    data = request.get_json()
    geojson_data = data.get('geojson_data')
    nombre_del_multi_polygon = data.get('nombre')
    
    try:
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
        cursor.close()
        conn.close()
        return jsonify({"message": "Polígono insertado correctamente"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/delete_polygon', methods=['DELETE'])
def delete_polygon():
    data = request.get_json()
    nombre = data.get('nombre')

    try:
        conn = conectar_a_base_de_datos()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM poligonos WHERE nombre = %s;", (nombre,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": f"Polígono '{nombre}' eliminado con éxito"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/replace_polygon', methods=['PUT'])
def replace_polygon():
    data = request.get_json()
    nombre_del_multi_polygon = data.get('nombre')
    geojson_data = data.get('geojson_data')

    try:
        polygons = [feature['geometry']['coordinates'] for feature in geojson_data['features']]
        multi_polygon = {"type": "MultiPolygon", "coordinates": polygons}
        nueva_geometria = json.dumps(multi_polygon)

        conn = conectar_a_base_de_datos()
        cursor = conn.cursor()

        cursor.execute(
            sql.SQL("DELETE FROM poligonos WHERE nombre = %s;"),
            (nombre_del_multi_polygon,)
        )
        cursor.execute(
            sql.SQL("INSERT INTO poligonos (nombre, geometria) VALUES (%s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326));"),
            (nombre_del_multi_polygon, nueva_geometria)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Polígono reemplazado correctamente"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/clasificar_direcciones', methods=['POST'])
def clasificar_direcciones():
    data = request.get_json()
    coordinates = data.get('coordinates')
    
    if not coordinates:
        return jsonify({"error": "No coordinates provided"}), 400

    try:
        conn = conectar_a_base_de_datos()
        poligonos = []

        with conn.cursor() as cursor:
            for coord in coordinates:
                lat = coord['lat']
                lon = coord['lon']
                cursor.execute("""
                SELECT nombre FROM poligonos
                WHERE ST_Intersects(geometria, ST_SetSRID(ST_MakePoint(%s, %s), 4326));
                """, (lon, lat))
                result = cursor.fetchone()
                poligonos.append(result[0] if result else "No clasificado")

        conn.close()
        return jsonify({"classification": poligonos}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)