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

def nombre_existe(nombre):
    conn = None
    try:
        conn = conectar_a_base_de_datos()
        cursor = conn.cursor()
        cursor.execute("SELECT nombre FROM poligonos WHERE LOWER(nombre) = LOWER(%s);", (nombre,))
        existe = cursor.fetchone()
        cursor.close()
        return existe[0] if existe else None
    except Exception as e:
        raise Exception(f"Error al verificar existencia del nombre: {str(e)}")
    finally:
        if conn:
            conn.close()

def partes_nombre_existen(nombre_parte, codigo_parte):
    conn = None
    try:
        conn = conectar_a_base_de_datos()
        cursor = conn.cursor()
        cursor.execute("""SELECT nombre FROM poligonos WHERE LOWER(SPLIT_PART(nombre, ' - ', 1)) = LOWER(%s) OR SPLIT_PART(nombre, ' - ', 2) = %s;""", (nombre_parte, codigo_parte))
        existe = cursor.fetchone()
        cursor.close()
        return existe[0] if existe else None
    except Exception as e:
        raise Exception(f"Error al verificar existencia de partes del nombre: {str(e)}")
    finally:
        if conn:
            conn.close()

def obtener_partes_nombre(nombre):
    partes = nombre.rsplit(' - ', 1)
    if len(partes) != 2:
        return None, None
    return partes[0].strip(), partes[1].strip()

@app.route('/insert_polygon', methods=['POST'])
def insert_polygon():
    data = request.get_json()
    geojson_data = data.get('geojson_data')
    nombre_del_multi_polygon = data.get('nombre')

    if not geojson_data or not nombre_del_multi_polygon:
        return jsonify({"error": "Faltan datos necesarios"}), 400
    
    nombre_del_multi_polygon = nombre_del_multi_polygon.lower()

    if not validar_nombre(nombre_del_multi_polygon):
        return jsonify({"error": "El nombre del polígono no cumple con la estructura requerida [Nombre del polígono - #######]"}), 400

    nombre_parte, codigo_parte = obtener_partes_nombre(nombre_del_multi_polygon)
    if not nombre_parte or not codigo_parte:
        return jsonify({"error": "El nombre del polígono no cumple con la estructura requerida [Nombre del polígono - #######]"}), 400

    if nombre_existe(nombre_del_multi_polygon):
        return jsonify({"error": f"El nombre del polígono '{nombre_del_multi_polygon}' ya existe"}), 400

    parte_existente = partes_nombre_existen(nombre_parte, codigo_parte)
    if parte_existente:
        return jsonify({"error": f"El nombre del polígono o el código '{parte_existente}' ya existen"}), 400

    # Validar que geojson_data tenga el formato esperado
    if 'features' not in geojson_data or not isinstance(geojson_data['features'], list):
        return jsonify({"error": "GeoJSON inválido"}), 400
    
    try:
        polygons = [feature['geometry']['coordinates'] for feature in geojson_data['features']]
        multi_polygon = {"type": "MultiPolygon", "coordinates": polygons}
        multi_polygon_json = json.dumps(multi_polygon)

        query = sql.SQL("INSERT INTO poligonos (nombre, geometria) VALUES (%s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326));")
        execute_query(query, (nombre_del_multi_polygon, multi_polygon_json))
        
        return jsonify({"message": "poligono insertado correctamente"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/delete_polygon', methods=['DELETE'])
def delete_polygon():
    data = request.get_json()
    nombre = data.get('nombre').lower()

    nombre_existente = nombre_existe(nombre)
    if not nombre_existente:
        return jsonify({"error": f"El poligono '{nombre}' no existe"}), 400

    try:
        query = "DELETE FROM poligonos WHERE LOWER(nombre) = LOWER(%s);"
        execute_query(query, (nombre,))
        
        return jsonify({"message": f"poligono '{nombre}' eliminado con éxito"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/replace_polygon', methods=['PUT'])
def replace_polygon():
    data = request.get_json()
    nombre_del_multi_polygon = data.get('nombre').lower()
    geojson_data = data.get('geojson_data')

    if not geojson_data or not nombre_del_multi_polygon:
        return jsonify({"error": "Faltan datos necesarios"}), 400
    
    if not validar_nombre(nombre_del_multi_polygon):
        return jsonify({"error": "El nombre del poligono no cumple con la estructura requerida [Nombre del poligono - #######]"}), 400

    nombre_existente = nombre_existe(nombre_del_multi_polygon)
    if not nombre_existente:
        return jsonify({"error": f"El poligono '{nombre_del_multi_polygon}' no existe"}), 400

    try:
        polygons = [feature['geometry']['coordinates'] for feature in geojson_data['features']]
        multi_polygon = {"type": "MultiPolygon", "coordinates": polygons}
        nueva_geometria = json.dumps(multi_polygon)

        conn = conectar_a_base_de_datos()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM poligonos WHERE LOWER(nombre) = LOWER(%s);", (nombre_del_multi_polygon,))
            cursor.execute("INSERT INTO poligonos (nombre, geometria) VALUES (%s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326));", (nombre_del_multi_polygon, nueva_geometria))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

        return jsonify({"message": "poligono reemplazado correctamente"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/update_polygon_name', methods=['PUT'])
def update_polygon_name():
    data = request.get_json()
    nombre_actual = data.get('nombre_actual').lower()
    nuevo_nombre = data.get('nuevo_nombre').lower()

    if not nombre_actual or not nuevo_nombre:
        return jsonify({"error": "Faltan datos necesarios"}), 400
    
    if not validar_nombre(nuevo_nombre):
        return jsonify({"error": "El nuevo nombre del poligono no cumple con la estructura requerida"}), 400

    nombre_existente = nombre_existe(nombre_actual)
    if not nombre_existente:
        return jsonify({"error": f"El poligono '{nombre_actual}' no existe"}), 400
    
    if nombre_existe(nuevo_nombre):
        return jsonify({"error": f"El poligono '{nuevo_nombre}' ya existe"}), 400

    nombre_parte, codigo_parte = obtener_partes_nombre(nuevo_nombre)
    if not nombre_parte or not codigo_parte:
        return jsonify({"error": "El nombre del poligono no cumple con la estructura requerida [Nombre del poligono - #######]"}), 400

    parte_existente = partes_nombre_existen(nombre_parte, codigo_parte)
    if parte_existente:
        return jsonify({"error": f"El nombre del poligono o el codigo '{parte_existente}' ya existen"}), 400

    try:
        query = "UPDATE poligonos SET nombre = %s WHERE LOWER(nombre) = LOWER(%s);"
        execute_query(query, (nuevo_nombre, nombre_actual))
        
        return jsonify({"message": f"Nombre del poligono '{nombre_actual}' actualizado a '{nuevo_nombre}'"}), 200

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
                if result:
                    nombre_completo = result[0]
                    partes_nombre = nombre_completo.split(' - ')
                    if len(partes_nombre) == 2:
                        glosa, codigo_postal = partes_nombre
                        poligonos.append({"glosa": glosa.strip(), "codigo_postal": codigo_postal.strip()})
                    else:
                        poligonos.append({"glosa": "Desconocido", "codigo_postal": "Desconocido"})
                else:
                    poligonos.append({"glosa": "No clasificado", "codigo_postal": "No clasificado"})

        return jsonify({"classification": poligonos}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/get_polygons', methods=['GET'])
def get_polygons():
    try:
        conn = conectar_a_base_de_datos()
        cursor = conn.cursor()
        cursor.execute("SELECT nombre FROM poligonos;")
        resultados = cursor.fetchall()
        cursor.close()
        conn.close()

        if not resultados:
            return jsonify({"poligonos": [], "message": "No hay polígonos en la base de datos"}), 200

        nombres_poligonos = [resultado[0] for resultado in resultados]

        return jsonify({"poligonos": nombres_poligonos}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
