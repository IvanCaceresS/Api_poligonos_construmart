import requests

# Datos para la solicitud
data = {
    "coordinates": [
        {"lat": -20.2307033, "lon": -70.1356692}
    ]
}

# Hacer la solicitud POST a la API
response = requests.post('http://192.168.56.1:5000/clasificar_direcciones', json=data)

# Mostrar la respuesta
print(response.json())
