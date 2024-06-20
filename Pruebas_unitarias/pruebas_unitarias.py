import requests
import json
from dotenv import load_dotenv
import os

# Cargar variables de entorno desde .env
load_dotenv('./.env')

# Variables de configuración obtenidas del archivo .env
API_URL = os.getenv('API_URL')
GEOJSON_FILE = os.getenv('GEOJSON_FILE')
GLOSA = os.getenv('GLOSA')
CODIGO_POSTAL = os.getenv('CODIGO_POSTAL')
NUEVA_GLOSA = os.getenv('NUEVA_GLOSA')
NUEVO_CODIGO_POSTAL = os.getenv('NUEVO_CODIGO_POSTAL')

resultados_pruebas = []

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

def enviar_solicitud(api_url, endpoint, method, data=None):
    url = f"{api_url}/{endpoint}"
    try:
        if method == 'POST':
            response = requests.post(url, json=data)
        elif method == 'PUT':
            response = requests.put(url, json=data)
        elif method == 'DELETE':
            response = requests.delete(url, json=data)
        elif method == 'GET':
            response = requests.get(url)
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

def probar_api(descripcion, endpoint, method, data=None):
    print(f"\n{descripcion}...")
    respuesta = enviar_solicitud(API_URL, endpoint, method, data)
    if respuesta:
        print(f"Respuesta de la API: {respuesta}")
        resultados_pruebas.append((descripcion, True))
    else:
        print("No se obtuvo una respuesta válida de la API.")
        resultados_pruebas.append((descripcion, False))

def probar_insert_polygon():
    geojson_data = cargar_geojson(GEOJSON_FILE)
    if not geojson_data:
        return

    data = {
        "geojson_data": geojson_data,
        "glosa": GLOSA,
        "codigo_postal": CODIGO_POSTAL
    }

    probar_api("Probando inserción de polígono", 'insert_polygon', 'POST', data)

def probar_delete_polygon(codigo_postal):
    data = {
        "codigo_postal": codigo_postal
    }

    probar_api("Probando eliminación de polígono", 'delete_polygon', 'DELETE', data)

def probar_replace_polygon():
    geojson_data = cargar_geojson(GEOJSON_FILE)
    if not geojson_data:
        return

    data = {
        "geojson_data": geojson_data,
        "codigo_postal": CODIGO_POSTAL
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
        "codigo_postal": CODIGO_POSTAL,
        "nueva_glosa": NUEVA_GLOSA
    }

    probar_api("Probando actualización de nombre de polígono", 'update_polygon_name', 'PUT', data)

def probar_actualizar_codigo_postal(codigo_postal_actual, nuevo_codigo_postal):
    data = {
        "codigo_postal_actual": codigo_postal_actual,
        "nuevo_codigo_postal": nuevo_codigo_postal
    }

    probar_api("Probando actualización de código postal de polígono", 'update_codigo_postal', 'PUT', data)

def probar_get_polygons():
    probar_api("Probando obtención de polígonos", 'get_polygons', 'GET')

def resumen_pruebas():
    total_pruebas = len(resultados_pruebas)
    pruebas_exitosas = sum(1 for _, resultado in resultados_pruebas if resultado)
    porcentaje_exitosas = (pruebas_exitosas / total_pruebas) * 100
    print("\nResumen de Pruebas:")
    print(f"Total de pruebas: {total_pruebas}")
    print(f"Pruebas exitosas: {pruebas_exitosas}")
    print(f"Porcentaje de éxito: {porcentaje_exitosas:.2f}%")

def main():
    print("-"*50)
    probar_insert_polygon()
    print("-"*50)
    probar_get_polygons()
    print("-"*50)
    probar_clasificar_direcciones()
    print("-"*50)
    probar_replace_polygon()
    print("-"*50)
    probar_actualizar_nombre_poligono()
    print("-"*50)
    probar_actualizar_codigo_postal(CODIGO_POSTAL, NUEVO_CODIGO_POSTAL)
    print("-"*50)
    probar_delete_polygon(NUEVO_CODIGO_POSTAL)
    print("-"*50)
    resumen_pruebas()
    print("-"*50)

if __name__ == '__main__':
    main()
