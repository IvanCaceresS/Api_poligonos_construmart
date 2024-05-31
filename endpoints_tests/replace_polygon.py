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

# Hacer la solicitud PUT a la API
response = requests.put('http://192.168.0.7:5000/replace_polygon', json=data)

# Mostrar la respuesta
print(response.json())
