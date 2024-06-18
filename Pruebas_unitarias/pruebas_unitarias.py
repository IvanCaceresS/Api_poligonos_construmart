import requests
import json
from dotenv import load_dotenv
import os

# Cargar variables de entorno desde .env
load_dotenv('./.env')

# Variables de configuración obtenidas del archivo .env
API_URL = os.getenv('API_URL')
GEOJSON_FILE = os.getenv('GEOJSON_FILE')
NOMBRE_POLIGONO = os.getenv('NOMBRE_POLIGONO')
NUEVO_NOMBRE_POLIGONO = os.getenv('NUEVO_NOMBRE_POLIGONO')

def cargar_geojson(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: El archivo {file_path} no se encontró.")
        return None
    except json.JSONDecodeError:
        print(f"Error: El archivo {file_path} no es un GeoJSON válido.")
        return None

def enviar_solicitud(api_url, endpoint, method, data):
    url = f"{api_url}/{endpoint}"
    try:
        if method == 'POST':
            response = requests.post(url, json=data)
        elif method == 'PUT':
            response = requests.put(url, json=data)
        elif method == 'DELETE':
            response = requests.delete(url, json=data)
        else:
            raise ValueError(f"Método HTTP no soportado: {method}")

        response.raise_for_status()  # Esto lanzará una excepción para códigos de estado HTTP 4xx/5xx
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"Error HTTP: {e.response.status_code} - {e.response.text}")
        return None
    except requests.exceptions.ConnectionError:
        print("Error de conexión. ¿Está el servidor corriendo?")
        return None
    except requests.exceptions.Timeout:
        print("La solicitud a la API ha tardado demasiado.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error en la solicitud a la API: {e}")
        return None

def probar_api(descripcion, endpoint, method, data):
    print(f"\n{descripcion}...")
    respuesta = enviar_solicitud(API_URL, endpoint, method, data)
    if respuesta:
        print(f"Respuesta de la API: {respuesta}")
    else:
        print("No se obtuvo una respuesta válida de la API.")

def probar_insert_polygon():
    geojson_data = cargar_geojson(GEOJSON_FILE)
    if not geojson_data:
        return

    data = {
        "geojson_data": geojson_data,
        "nombre": NOMBRE_POLIGONO
    }

    probar_api("Probando inserción de polígono", 'insert_polygon', 'POST', data)

def probar_delete_polygon(nombre):
    data = {
        "nombre": nombre
    }

    probar_api("Probando eliminación de polígono", 'delete_polygon', 'DELETE', data)

def probar_replace_polygon():
    geojson_data = cargar_geojson(GEOJSON_FILE)
    if not geojson_data:
        return

    data = {
        "geojson_data": geojson_data,
        "nombre": NOMBRE_POLIGONO
    }

    probar_api("Probando reemplazo de polígono", 'replace_polygon', 'PUT', data)

def probar_clasificar_direcciones():
    data = {
        "coordinates": [
            {"lat": -20.2307033, "lon": -70.1356692}
        ]
    }

    probar_api("Probando clasificación de direcciones", 'clasificar_direcciones', 'POST', data)

def probar_actualizar_nombre_poligono():
    data = {
        "nombre_actual": NOMBRE_POLIGONO,
        "nuevo_nombre": NUEVO_NOMBRE_POLIGONO
    }

    probar_api("Probando actualización de nombre de polígono", 'update_polygon_name', 'PUT', data)

def main():
    probar_insert_polygon()
    probar_clasificar_direcciones()
    probar_replace_polygon()
    probar_actualizar_nombre_poligono()
    probar_delete_polygon(NUEVO_NOMBRE_POLIGONO)

if __name__ == '__main__':
    main()
