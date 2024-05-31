import pandas as pd
import requests

# Crear un DataFrame con las coordenadas
data = {
    "Latitud": [-20.2307033],
    "Longitud": [-70.1356692]
}

df = pd.DataFrame(data)

# Guardar el DataFrame como un archivo Excel
excel_path = 'direcciones.xlsx'
df.to_excel(excel_path, index=False)

# Datos para la solicitud
data = {
    "file_path": excel_path
}

# Hacer la solicitud POST a la API
response = requests.post('http://127.0.0.1:5000/clasificar_direcciones', json=data)

# Mostrar la respuesta
print(response.json())
