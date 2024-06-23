# API de Clasificación de Direcciones y Polígonos

Esta API permite insertar, reemplazar, eliminar polígonos y cambiar el nombre de un polígono, así como clasificar coordenadas geográficas dentro de estos polígonos. La API está construida con Flask y se conecta a una base de datos PostgreSQL con PostGIS.

## Requisitos

- Python 3.12.2
- Flask 2.3.2
- psycopg2-binary 2.9.9
- requests 2.31.0
- python-dotenv 1.0.0

## Instalación

1. Clona el repositorio o descarga los archivos.

2. Instala las dependencias necesarias usando `requirements.txt`:
    ```sh
    pip install -r requirements.txt
    ```

3. Asegúrate de que tienes un archivo `.env` en el directorio `resources/` con las credenciales de tu base de datos PostgreSQL. Debe contener las siguientes variables:
    ```env
    DB_USER=tu_usuario
    DB_PASSWORD=tu_contraseña
    DB_HOST=tu_host
    DB_PORT=5432
    DB_NAME=tu_nombre_de_base_de_datos
    ```

4. Asegúrate de que tienes un archivo `.env` en el directorio `Pruebas_unitarias/` con la configuración de la API. Debe contener las siguientes variables:
    ```env
    API_URL=http://xxx.xxx.xxx.xxx:5000
    GEOJSON_FILE=Iquique zona (1).geojson
    GLOSA=Iquique Zona 1
    CODIGO_POSTAL=1234567
    NUEVA_GLOSA=Nuevo Iquique Zona 1
    NUEVO_CODIGO_POSTAL=7654321
    ```

5. Configura tu base de datos PostgreSQL con PostGIS y la tabla necesaria:
    ```sql
    CREATE EXTENSION IF NOT EXISTS postgis;
    CREATE EXTENSION IF NOT EXISTS citext;

    CREATE TABLE IF NOT EXISTS public.poligonos
    (
        codigo_postal VARCHAR(7) PRIMARY KEY,
        glosa CITEXT,
        geometria GEOMETRY(MultiPolygon, 4326)
    );

    ALTER TABLE public.poligonos
        OWNER TO postgres;
    ```

## Uso

1. Inicia el servidor Flask:
    ```sh
    python app.py
    ```
   Deberías ver un mensaje que indica que el servidor está corriendo en `http://0.0.0.0:5000`.

2. Prueba cada una de las rutas usando los programas proporcionados en `Pruebas_unitarias`:

### Tanto para probrar: Insertar Polígono, Clasificar Direcciones, Reemplazar Polígono, Eliminar Polígono, Actualizar Nombre de Polígono y Ver Poligonos existentes
1. Ejecuta el programa:
    ```sh
    python pruebas_unitarias.py
    ```

## Notas

- Asegúrate de que el archivo `Iquique zona (1).geojson` esté en el mismo directorio desde donde estás ejecutando estos programas, o proporciona las URLs correctas para realizar las pruebas.
- Si el servidor Flask no está corriendo, no podrás hacer las solicitudes a la API. Asegúrate de que el servidor está corriendo antes de ejecutar los programas.
- Reemplaza `http://<your-server-ip>:5000` con la dirección IP de tu servidor si estás ejecutando los programas en una máquina diferente de donde se ejecuta la API.
- Asegúrate de que el puerto 5000 del servidor pueda ser visible y permita conexiones.


