# Mis finanzas

Aplicación web para saber cuánto dinero queda disponible en el mes, cuánto se puede gastar por día y si una compra entra en el presupuesto. Cada persona se registra con un email y una contraseña, carga sus ingresos y gastos, y ve únicamente sus propios datos.

Trabajo práctico grupal de las Unidades 3 y 4 (resuelto de forma individual).

## Direcciones publicadas

- Aplicación: https://eber.pythonanywhere.com
- Tablero: [https://tp2-finanzas-tablero.onrender.com/ ]
- Repositorio: https://github.com/Eberalej/tp2-finanzas

## Qué hace

- Registro e inicio de sesión (contraseñas guardadas con hash).
- Carga de ingresos y gastos, con validación en el navegador y en el servidor.
- Panel con el saldo del mes, el gasto diario disponible y las cotizaciones del dólar oficial y blue.
- Simulador de compra: calcula cómo quedaría el mes si se hiciera una compra, en pesos o en dólares.
- Tablero con Streamlit y Pandas: gastos por categoría, ingresos y gastos por mes y tabla de movimientos.

## Tecnologías

- Python, Flask y plantillas Jinja2
- SQLite
- `requests`, para consultar DolarAPI y la API del BCRA (con tiempo máximo de espera y respaldo si un servicio falla)
- Streamlit y Pandas

## Estructura

```
app.py                  Aplicación Flask (rutas y API)
db.py                   Conexión y tablas de SQLite
servicios.py            Consulta de cotizaciones con requests
requirements.txt        Dependencias de la aplicación
templates/              Plantillas HTML (heredan de base.html)
static/estilo.css       Estilos
tablero/dashboard.py    Tablero de Streamlit
tablero/requirements.txt  Dependencias del tablero
.streamlit/config.toml  Colores del tablero
.env.example            Ejemplo de variables de entorno
```

## Cómo ejecutarlo en una computadora con Windows

1. Crear y activar un entorno virtual:

```
python -m venv venv
venv\Scripts\activate
```

2. Instalar las dependencias:

```
pip install -r requirements.txt
```

3. Crear el archivo `.env` a partir del ejemplo y completar `SECRET_KEY` con una frase larga y propia:

```
copy .env.example .env
```

4. Ejecutar la aplicación:

```
python app.py
```

Queda disponible en http://127.0.0.1:5000. La base de datos (`finanzas.db`) se crea sola la primera vez.

5. Para el tablero, en otra terminal con el entorno activado:

```
pip install -r tablero/requirements.txt
streamlit run tablero/dashboard.py
```

El tablero toma la dirección de la aplicación de la variable `URL_FLASK` del `.env` y se inicia sesión con una cuenta creada en esa aplicación.

## Puntos de acceso JSON

Requieren haber iniciado sesión. Sin sesión responden con el código 401.

| Dirección | Qué devuelve |
|---|---|
| `/api/resumen` | Ingresos, gastos, saldo y gastos por categoría del mes actual |
| `/api/movimientos` | Lista de movimientos del usuario |

## Variables de entorno

| Variable | Para qué sirve |
|---|---|
| `SECRET_KEY` | Firma la sesión de Flask. Va en el `.env`, que no se sube ni se entrega. |
| `URL_FLASK` | Dirección de la aplicación a la que se conecta el tablero. |

Las dos APIs de cotización que se usan (DolarAPI y BCRA) son públicas y no necesitan clave.


## Publicación

La aplicación Flask está en PythonAnywhere y el tablero de Streamlit en Render (plan gratuito).

- La clave de la sesión de Flask (`SECRET_KEY`) está en el `.env` del servidor de PythonAnywhere.
- La dirección de la aplicación se carga en el tablero como variable de entorno `URL_FLASK`, desde el panel de Render.
- Ningún secreto está en el repositorio.

Configuración del tablero en Render:

- Build Command: `pip install -r requirements.txt`
- Start Command: `python -m streamlit run dashboard.py --server.port $PORT --server.address 0.0.0.0 --server.headless true` 
- Variable de entorno: `URL_FLASK` con la dirección de la aplicación

Nota: en el plan gratuito de Render, el tablero se apaga tras un rato sin visitas y la primera vez puede tardar alrededor de un minuto en abrir.