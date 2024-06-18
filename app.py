from flask import Flask, request, jsonify
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
    try:
        DB_USER = os.getenv("DB_USER")
        DB_PASSWORD = os.getenv("DB_PASSWORD")
        DB_HOST = os.getenv("DB_HOST")
        DB_PORT = os.getenv("DB_PORT")
        DB_NAME = os.getenv("DB_NAME")
        return psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
    except Exception as e:
        raise ConnectionError(f"Error al conectar a la base de datos: {str(e)}")

def execute_query(query, params):
    conn = None
    try:
        conn = conectar_a_base_de_datos()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        cursor.close()
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        raise Exception(f"Error en la base de datos: {e.pgcode} - {e.pgerror}")
    except Exception as e:
        if conn:
            conn.rollback()
        raise Exception(f"Error: {str(e)}")
    finally:
        if conn:
            conn.close()

def validar_nombre(nombre):
    patron = re.compile(r"^[\w\sáéíóúÁÉÍÓÚñÑüÜ]+ - \d{7}$")
    return patron.match(nombre) is not None

@app.route('/insert_polygon', methods=['POST'])
def insert_polygon():
    data = request.get_json()
    geojson_data = data.get('geojson_data')
    nombre_del_multi_polygon = data.get('nombre')

    if not geojson_data or not nombre_del_multi_polygon:
        return jsonify({"error": "Faltan datos necesarios"}), 400
    
    if not validar_nombre(nombre_del_multi_polygon):
        return jsonify({"error": "El nombre del polígono no cumple con la estructura requerida"}), 400

    # Validar que geojson_data tenga el formato esperado
    if 'features' not in geojson_data or not isinstance(geojson_data['features'], list):
        return jsonify({"error": "GeoJSON inválido"}), 400
    
    try:
        polygons = [feature['geometry']['coordinates'] for feature in geojson_data['features']]
        multi_polygon = {"type": "MultiPolygon", "coordinates": polygons}
        multi_polygon_json = json.dumps(multi_polygon)

        query = sql.SQL("INSERT INTO poligonos (nombre, geometria) VALUES (%s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326));")
        execute_query(query, (nombre_del_multi_polygon, multi_polygon_json))
        
        return jsonify({"message": "Polígono insertado correctamente"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/delete_polygon', methods=['DELETE'])
def delete_polygon():
    data = request.get_json()
    nombre = data.get('nombre')

    try:
        query = "DELETE FROM poligonos WHERE nombre = %s;"
        execute_query(query, (nombre,))
        
        return jsonify({"message": f"Polígono '{nombre}' eliminado con éxito"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/replace_polygon', methods=['PUT'])
def replace_polygon():
    data = request.get_json()
    nombre_del_multi_polygon = data.get('nombre')
    geojson_data = data.get('geojson_data')

    if not geojson_data or not nombre_del_multi_polygon:
        return jsonify({"error": "Faltan datos necesarios"}), 400
    
    if not validar_nombre(nombre_del_multi_polygon):
        return jsonify({"error": "El nombre del polígono no cumple con la estructura requerida"}), 400

    try:
        polygons = [feature['geometry']['coordinates'] for feature in geojson_data['features']]
        multi_polygon = {"type": "MultiPolygon", "coordinates": polygons}
        nueva_geometria = json.dumps(multi_polygon)

        conn = conectar_a_base_de_datos()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM poligonos WHERE nombre = %s;", (nombre_del_multi_polygon,))
            cursor.execute("INSERT INTO poligonos (nombre, geometria) VALUES (%s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326));", (nombre_del_multi_polygon, nueva_geometria))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

        return jsonify({"message": "Polígono reemplazado correctamente"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/update_polygon_name', methods=['PUT'])
def update_polygon_name():
    data = request.get_json()
    nombre_actual = data.get('nombre_actual')
    nuevo_nombre = data.get('nuevo_nombre')

    if not nombre_actual or not nuevo_nombre:
        return jsonify({"error": "Faltan datos necesarios"}), 400
    
    if not validar_nombre(nuevo_nombre):
        return jsonify({"error": "El nuevo nombre del polígono no cumple con la estructura requerida"}), 400

    try:
        query = "UPDATE poligonos SET nombre = %s WHERE nombre = %s;"
        execute_query(query, (nuevo_nombre, nombre_actual))
        
        return jsonify({"message": f"Nombre del polígono '{nombre_actual}' actualizado a '{nuevo_nombre}'"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/clasificar_direcciones', methods=['POST'])
def clasificar_direcciones():
    data = request.get_json()
    coordinates = data.get('coordinates')
    
    if not coordinates:
        return jsonify({"error": "No coordinates provided"}), 400

    conn = None
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

        return jsonify({"classification": poligonos}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
