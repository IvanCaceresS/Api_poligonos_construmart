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

def validar_glosa(glosa):
    return glosa is not None and glosa.strip() != ""

def validar_codigo_postal(codigo_postal):
    patron = re.compile(r"^\d{7}$")
    return patron.match(str(codigo_postal)) is not None

def codigo_postal_existe(codigo_postal):
    conn = None
    try:
        conn = conectar_a_base_de_datos()
        cursor = conn.cursor()
        cursor.execute("SELECT codigo_postal FROM poligonos WHERE codigo_postal = %s;", (str(codigo_postal),))
        existe = cursor.fetchone()
        cursor.close()
        return existe[0] if existe else None
    except Exception as e:
        raise Exception(f"Error al verificar existencia del código postal: {str(e)}")
    finally:
        if conn:
            conn.close()

@app.route('/insert_polygon', methods=['POST'])
def insert_polygon():
    data = request.get_json()
    geojson_data = data.get('geojson_data')
    glosa = data.get('glosa')
    codigo_postal = data.get('codigo_postal')

    if not geojson_data or not glosa or not codigo_postal:
        return jsonify({"error": "Faltan datos necesarios"}), 400

    if not validar_glosa(glosa) or not validar_codigo_postal(codigo_postal):
        return jsonify({"error": "La glosa no puede estar vacía y el código postal debe ser numérico de 7 dígitos"}), 400

    if codigo_postal_existe(codigo_postal):
        return jsonify({"error": f"El código postal '{codigo_postal}' ya existe"}), 400

    # Validar que geojson_data tenga el formato esperado
    if 'features' not in geojson_data or not isinstance(geojson_data['features'], list):
        return jsonify({"error": "GeoJSON inválido"}), 400

    try:
        polygons = [feature['geometry']['coordinates'] for feature in geojson_data['features']]
        multi_polygon = {"type": "MultiPolygon", "coordinates": polygons}
        multi_polygon_json = json.dumps(multi_polygon)

        query = sql.SQL("INSERT INTO poligonos (codigo_postal, glosa, geometria) VALUES (%s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326));")
        execute_query(query, (codigo_postal, glosa, multi_polygon_json))
        
        return jsonify({"message": "Polígono insertado correctamente"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/delete_polygon', methods=['DELETE'])
def delete_polygon():
    data = request.get_json()
    codigo_postal = data.get('codigo_postal')

    codigo_postal_existente = codigo_postal_existe(codigo_postal)
    if not codigo_postal_existente:
        return jsonify({"error": f"El código postal '{codigo_postal}' no existe"}), 400

    try:
        query = "DELETE FROM poligonos WHERE codigo_postal = %s;"
        execute_query(query, (codigo_postal,))
        
        return jsonify({"message": f"Polígono con código postal '{codigo_postal}' eliminado con éxito"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/replace_polygon', methods=['PUT'])
def replace_polygon():
    data = request.get_json()
    codigo_postal = data.get('codigo_postal')
    geojson_data = data.get('geojson_data')

    if not geojson_data or not codigo_postal:
        return jsonify({"error": "Faltan datos necesarios"}), 400

    if not validar_codigo_postal(codigo_postal):
        return jsonify({"error": "El código postal debe ser numérico de 7 dígitos"}), 400

    codigo_postal_existente = codigo_postal_existe(codigo_postal)
    if not codigo_postal_existente:
        return jsonify({"error": f"El código postal '{codigo_postal}' no existe"}), 400

    try:
        polygons = [feature['geometry']['coordinates'] for feature in geojson_data['features']]
        multi_polygon = {"type": "MultiPolygon", "coordinates": polygons}
        nueva_geometria = json.dumps(multi_polygon)

        conn = conectar_a_base_de_datos()
        cursor = conn.cursor()
        try:
            query = """
            UPDATE poligonos
            SET geometria = ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)
            WHERE codigo_postal = %s;
            """
            cursor.execute(query, (nueva_geometria, codigo_postal))
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
    codigo_postal = data.get('codigo_postal')
    nueva_glosa = data.get('nueva_glosa')

    if not codigo_postal or not nueva_glosa:
        return jsonify({"error": "Faltan datos necesarios"}), 400

    if not validar_glosa(nueva_glosa):
        return jsonify({"error": "La nueva glosa no puede estar vacía"}), 400

    codigo_postal_existente = codigo_postal_existe(codigo_postal)
    if not codigo_postal_existente:
        return jsonify({"error": f"El código postal '{codigo_postal}' no existe"}), 400

    try:
        query = "UPDATE poligonos SET glosa = %s WHERE codigo_postal = %s;"
        execute_query(query, (nueva_glosa, codigo_postal))
        
        return jsonify({"message": f"Nombre del polígono con código postal '{codigo_postal}' actualizado a '{nueva_glosa}'"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/update_codigo_postal', methods=['PUT'])
def update_codigo_postal():
    data = request.get_json()
    codigo_postal_actual = data.get('codigo_postal_actual')
    nuevo_codigo_postal = data.get('nuevo_codigo_postal')

    if not codigo_postal_actual or not nuevo_codigo_postal:
        return jsonify({"error": "Faltan datos necesarios"}), 400

    if not validar_codigo_postal(codigo_postal_actual) or not validar_codigo_postal(nuevo_codigo_postal):
        return jsonify({"error": "Ambos códigos postales deben ser numéricos de 7 dígitos"}), 400

    if codigo_postal_actual == nuevo_codigo_postal:
        return jsonify({"error": "El nuevo código postal no puede ser igual al código postal actual"}), 400

    codigo_postal_existente = codigo_postal_existe(codigo_postal_actual)
    if not codigo_postal_existente:
        return jsonify({"error": f"El código postal actual '{codigo_postal_actual}' no existe"}), 400

    nuevo_codigo_postal_existente = codigo_postal_existe(nuevo_codigo_postal)
    if nuevo_codigo_postal_existente:
        return jsonify({"error": f"El nuevo código postal '{nuevo_codigo_postal}' ya existe"}), 400

    try:
        conn = conectar_a_base_de_datos()
        cursor = conn.cursor()
        try:
            query = """
            UPDATE poligonos
            SET codigo_postal = %s
            WHERE codigo_postal = %s;
            """
            cursor.execute(query, (nuevo_codigo_postal, codigo_postal_actual))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

        return jsonify({"message": "Código postal actualizado correctamente"}), 200

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
                SELECT glosa, codigo_postal FROM poligonos
                WHERE ST_Intersects(geometria, ST_SetSRID(ST_MakePoint(%s, %s), 4326));
                """, (lon, lat))
                result = cursor.fetchone()
                if result:
                    glosa, codigo_postal = result
                    poligonos.append({"glosa": glosa, "codigo_postal": codigo_postal})
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
        cursor.execute("SELECT glosa, codigo_postal FROM poligonos;")
        resultados = cursor.fetchall()
        cursor.close()
        conn.close()

        if not resultados:
            return jsonify({"poligonos": [], "message": "No hay polígonos en la base de datos"}), 200

        poligonos = [{"glosa": resultado[0], "codigo_postal": resultado[1]} for resultado in resultados]

        return jsonify({"poligonos": poligonos}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)