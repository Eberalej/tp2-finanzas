import os
import requests
import pandas as pd
import streamlit as st
from dotenv import load_dotenv


load_dotenv()


def leer_url_flask():
    url = os.getenv("URL_FLASK")
    if not url:
        try:
            url = st.secrets["URL_FLASK"]
        except Exception:
            url = "http://127.0.0.1:5000"
    return url.rstrip("/")


URL_FLASK = leer_url_flask()


st.set_page_config(page_title="Tablero de finanzas")
st.title("Tablero de finanzas")


def pesos(numero):
    """Formatea un número como 1.500.000 (con puntos)."""
    return "$ " + f"{numero:,.0f}".replace(",", ".")


def iniciar_sesion(email, password):
    """Inicia sesión en la app Flask. Devuelve (sesion, mensaje_de_error)."""
    sesion = requests.Session()
    try:
        sesion.post(
            URL_FLASK + "/login",
            data={"email": email, "password": password},
            timeout=10,
        )
        prueba = sesion.get(URL_FLASK + "/api/resumen", timeout=10)
    except requests.exceptions.Timeout:
        return None, "La aplicación tardó demasiado en responder."
    except requests.exceptions.RequestException:
        return None, "No se pudo conectar con la aplicación. ¿Está encendida?"

    if prueba.status_code != 200:
        return None, "Email o contraseña incorrectos."
    return sesion, None


def pedir_json(ruta):
    """Pide datos a la API de Flask. Devuelve None si algo falla."""
    try:
        respuesta = st.session_state["sesion"].get(URL_FLASK + ruta, timeout=10)
        respuesta.raise_for_status()
        return respuesta.json()
    except requests.exceptions.RequestException:
        return None


if "sesion" not in st.session_state:
    st.session_state["sesion"] = None

# ---------- Pantalla de inicio de sesión ----------
if st.session_state["sesion"] is None:
    st.subheader("Iniciá sesión con tu cuenta")
    with st.form("login"):
        email = st.text_input("Email")
        password = st.text_input("Contraseña", type="password")
        enviado = st.form_submit_button("Entrar")

    if enviado:
        sesion, error = iniciar_sesion(email.strip().lower(), password)
        if error:
            st.error(error)
        else:
            st.session_state["sesion"] = sesion
            st.rerun()
    st.stop()

# ---------- Tablero ----------
if st.button("Cerrar sesión"):
    st.session_state["sesion"] = None
    st.rerun()

resumen = pedir_json("/api/resumen")
movimientos = pedir_json("/api/movimientos")

if resumen is None or movimientos is None:
    st.error("No se pudieron obtener los datos. Cerrá sesión e intentá de nuevo.")
    st.stop()

st.subheader("Resumen de " + resumen["mes"])
col1, col2, col3, col4 = st.columns(4)
col1.metric("Ingresos", pesos(resumen["ingresos"]))
col2.metric("Gastos", pesos(resumen["gastos"]))
col3.metric("Te queda", pesos(resumen["saldo"]))
col4.metric("Por día", pesos(resumen["por_dia"]))

st.subheader("Gastos del mes por categoría")
gastos_categoria = resumen["gastos_por_categoria"]
if gastos_categoria:
    df_categorias = pd.DataFrame(
        {
            "categoria": list(gastos_categoria.keys()),
            "total": list(gastos_categoria.values()),
        }
    ).set_index("categoria")
    st.bar_chart(df_categorias)
else:
    st.info("Todavía no hay gastos cargados este mes.")

if not movimientos:
    st.info("Todavía no cargaste movimientos.")
    st.stop()

df = pd.DataFrame(movimientos)
df["fecha"] = pd.to_datetime(df["fecha"])
df["mes"] = df["fecha"].dt.strftime("%Y-%m")

st.subheader("Ingresos y gastos por mes")
por_mes = df.pivot_table(
    index="mes", columns="tipo", values="monto", aggfunc="sum", fill_value=0
)
st.bar_chart(por_mes)

st.subheader("Todos tus movimientos")
tabla = df[["fecha", "tipo", "descripcion", "categoria", "monto"]].copy()
tabla["fecha"] = tabla["fecha"].dt.strftime("%Y-%m-%d")
st.dataframe(tabla, hide_index=True)