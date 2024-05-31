import requests

# Datos para la solicitud
data = {
    "nombre": "Iquique Zona 1 - 1234567"
}

# Hacer la solicitud DELETE a la API
response = requests.delete('http://192.168.0.7:5000/delete_polygon', json=data)

# Mostrar la respuesta
print(response.json())
