import requests
import json

# Leer el archivo geojson
with open('Iquique zona (1).geojson', 'r', encoding='utf-8') as f:
    geojson_data = json.load(f)

# Datos para la solicitud
data = {
    "geojson_data": geojson_data,
    "nombre": "Iquique Zona 1 - 1234567"
}

# Hacer la solicitud POST a la API
response = requests.post('http://127.0.0.1:5000/insert_polygon', json=data)

# Mostrar la respuesta
print(response.json())
