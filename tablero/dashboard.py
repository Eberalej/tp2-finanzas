import html
import os

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


#def leer_url_flask():
    #url = os.getenv("URL_FLASK")
    #if not url:
        #try:
            #url = st.secrets["URL_FLASK"]
        #except Exception:
            #url = "http://127.0.0.1:5000"
    #return url.rstrip("/")


URL_PUBLICADA = "https://eber.pythonanywhere.com"

def leer_url_flask():
    url = os.getenv("URL_FLASK")
    if not url:
        try:
            url = st.secrets["URL_FLASK"]
        except Exception:
            url = URL_PUBLICADA
    return url.rstrip("/")


URL_FLASK = leer_url_flask()

st.set_page_config(page_title="Tablero de finanzas", layout="wide")

ESTILO = """
<style>
div.block-container, [data-testid="stMainBlockContainer"] { max-width: 1400px; }
.tb-titulo { margin: 0; font-size: 1.9rem; font-weight: 700; color: #0f172a; }
.tb-sub { margin: 0 0 18px 0; color: #64748b; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.08em; }
.tb-hero { display: grid; grid-template-columns: 1.4fr 1fr; gap: 20px; padding: 28px; border-radius: 18px; background: linear-gradient(135deg, #0f172a 0%, #115e59 100%); box-shadow: 0 8px 24px rgba(15, 23, 42, 0.12); }
.tb-hero.tb-alerta { background: linear-gradient(135deg, #450a0a 0%, #b91c1c 100%); }
.tb-hero .tb-etiqueta { display: block; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; color: rgba(255, 255, 255, 0.75); }
.tb-hero .tb-grande { display: block; margin-top: 6px; font-size: clamp(1.8rem, 6vw, 2.9rem); line-height: 1.1; font-weight: 700; color: #ffffff; overflow-wrap: anywhere; }
.tb-hero .tb-dia { display: block; margin-top: 6px; font-size: clamp(1.4rem, 4.5vw, 2rem); font-weight: 700; color: #5eead4; overflow-wrap: anywhere; }
.tb-hero .tb-nota { display: block; margin-top: 2px; font-size: 0.85rem; color: rgba(255, 255, 255, 0.75); }
.tb-lado { border-left: 1px solid rgba(255, 255, 255, 0.2); padding-left: 20px; }
.tb-tarjetas { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin-top: 14px; }
.tb-tarjeta { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 18px; box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08); }
.tb-tarjeta .tb-etiqueta { display: block; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em; color: #64748b; }
.tb-tarjeta .tb-valor { display: block; margin-top: 6px; font-size: clamp(1.3rem, 4vw, 1.7rem); font-weight: 700; color: #0f172a; overflow-wrap: anywhere; }
.tb-tarjeta .tb-valor.tb-verde { color: #059669; }
.tb-tarjeta .tb-valor.tb-rojo { color: #dc2626; }
.tb-tarjeta .tb-detalle { display: block; margin-top: 6px; font-size: 0.9rem; color: #64748b; }
.tb-barra { height: 12px; margin-top: 12px; background: #e2e8f0; border-radius: 999px; overflow: hidden; }
.tb-relleno { height: 100%; background: #0f766e; border-radius: 999px; }
.tb-relleno.tb-pasado { background: #dc2626; }
@media (max-width: 640px) {
.tb-hero { grid-template-columns: 1fr; padding: 20px; }
.tb-lado { border-left: none; border-top: 1px solid rgba(255, 255, 255, 0.2); padding: 14px 0 0 0; }
}
</style>
"""

st.markdown(ESTILO, unsafe_allow_html=True)
st.markdown(
    '<h1 class="tb-titulo">Mis finanzas</h1>'
    '<p class="tb-sub">Tablero</p>',
    unsafe_allow_html=True,
)


def pesos(numero):
    """Formatea un número como $ 1.500.000 (con puntos)."""
    return "$ " + f"{numero:,.0f}".replace(",", ".")


def tarjeta(etiqueta, valor, clase="", detalle=""):
    texto_detalle = (
        f'<span class="tb-detalle">{html.escape(detalle)}</span>' if detalle else ""
    )
    return (
        '<div class="tb-tarjeta">'
        f'<span class="tb-etiqueta">{html.escape(etiqueta)}</span>'
        f'<span class="tb-valor {clase}">{html.escape(valor)}</span>'
        f"{texto_detalle}"
        "</div>"
    )


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


def cargar_datos():
    """Pide el resumen y los movimientos. Devuelve None si algo falla."""
    resumen = pedir_json("/api/resumen")
    movimientos = pedir_json("/api/movimientos")
    if resumen is None or movimientos is None:
        return None
    return {"resumen": resumen, "movimientos": movimientos}


if "sesion" not in st.session_state:
    st.session_state["sesion"] = None
if "datos" not in st.session_state:
    st.session_state["datos"] = None

# ---------- Pantalla de inicio de sesión ----------
if st.session_state["sesion"] is None:
    _, centro, _ = st.columns([1, 1.2, 1])
    with centro:
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

# ---------- Barra lateral: acciones ----------
with st.sidebar:
    st.header("Opciones")
    if st.button("Actualizar datos"):
        st.session_state["datos"] = cargar_datos()
    if st.button("Cerrar sesión"):
        st.session_state["sesion"] = None
        st.session_state["datos"] = None
        st.rerun()

if st.session_state["datos"] is None:
    st.session_state["datos"] = cargar_datos()

datos = st.session_state["datos"]
if datos is None:
    st.error("No se pudieron obtener los datos. Cerrá sesión e intentá de nuevo.")
    st.stop()

resumen = datos["resumen"]
movimientos = datos["movimientos"]
mes_actual = resumen["mes"]

if not movimientos:
    st.info(
        "Todavía no cargaste movimientos. Cargalos en la aplicación "
        "y después tocá Actualizar datos."
    )
    st.stop()

df = pd.DataFrame(movimientos)
df["fecha"] = pd.to_datetime(df["fecha"])
df["mes"] = df["fecha"].dt.strftime("%Y-%m")

# ---------- Barra lateral: filtros ----------
meses = sorted(set(df["mes"]) | {mes_actual}, reverse=True)
categorias_todas = sorted(df["categoria"].unique())

with st.sidebar:
    st.divider()
    st.header("Filtros")
    mes = st.selectbox("Mes", meses, index=meses.index(mes_actual))
    categorias = st.multiselect(
        "Categorías", categorias_todas, default=categorias_todas
    )
    st.caption(
        "El mes elegido cambia las tarjetas y los gráficos. "
        "Las categorías filtran los gráficos y la tabla."
    )

df_mes = df[df["mes"] == mes]
ingresos = float(df_mes.loc[df_mes["tipo"] == "ingreso", "monto"].sum())
gastos = float(df_mes.loc[df_mes["tipo"] == "gasto", "monto"].sum())
saldo = ingresos - gastos
es_actual = mes == mes_actual

# ---------- Tarjeta principal ----------
st.markdown(f'<p class="tb-sub">Resumen de {mes}</p>', unsafe_allow_html=True)

if es_actual and saldo > 0:
    clase_hero = "tb-hero"
    etiqueta_hero = "Te queda este mes"
    lado = (
        '<span class="tb-etiqueta">Podés gastar por día</span>'
        f'<span class="tb-dia">{pesos(resumen["por_dia"])}</span>'
        f'<span class="tb-nota">durante {resumen["dias_restantes"]} días</span>'
    )
elif saldo > 0:
    clase_hero = "tb-hero"
    etiqueta_hero = "Saldo de " + mes
    lado = (
        '<span class="tb-etiqueta">Mes cerrado</span>'
        '<span class="tb-dia">Terminó con saldo a favor</span>'
    )
else:
    clase_hero = "tb-hero tb-alerta"
    etiqueta_hero = "Te queda este mes" if es_actual else "Saldo de " + mes
    lado = (
        '<span class="tb-etiqueta">Atención</span>'
        '<span class="tb-dia">Sin saldo disponible</span>'
        '<span class="tb-nota">Se gastó todo lo que ingresó en el mes</span>'
    )

st.markdown(
    f'<div class="{clase_hero}" translate="no">'
    "<div>"
    f'<span class="tb-etiqueta">{etiqueta_hero}</span>'
    f'<span class="tb-grande">{pesos(saldo)}</span>'
    "</div>"
    f'<div class="tb-lado">{lado}</div>'
    "</div>",
    unsafe_allow_html=True,
)

# ---------- Tarjetas secundarias ----------
gastos_cat = (
    df_mes[df_mes["tipo"] == "gasto"]
    .groupby("categoria")["monto"]
    .sum()
    .sort_values(ascending=False)
)

if not gastos_cat.empty:
    top_nombre = str(gastos_cat.index[0])
    top_monto = float(gastos_cat.iloc[0])
    top_detalle = f"{pesos(top_monto)} ({top_monto / gastos * 100:.0f}% de tus gastos)"
else:
    top_nombre = "—"
    top_detalle = "Sin gastos este mes"

st.markdown(
    '<div class="tb-tarjetas" translate="no">'
    + tarjeta("Ingresos del mes", pesos(ingresos), "tb-verde")
    + tarjeta("Gastos del mes", pesos(gastos), "tb-rojo")
    + tarjeta("Movimientos del mes", str(len(df_mes)))
    + tarjeta("Categoría con más gasto", top_nombre, "", top_detalle)
    + "</div>",
    unsafe_allow_html=True,
)

if ingresos > 0:
    porcentaje = gastos / ingresos * 100
    ancho = min(porcentaje, 100)
    clase_barra = "tb-relleno tb-pasado" if porcentaje > 100 else "tb-relleno"
    uso = (
        f'<span class="tb-detalle">Gastaste el {porcentaje:.0f}% de lo que ingresó este mes.</span>'
        f'<div class="tb-barra"><div class="{clase_barra}" style="width: {ancho:.0f}%"></div></div>'
    )
else:
    uso = '<span class="tb-detalle">Todavía no hay ingresos en este mes.</span>'

st.markdown(
    '<div class="tb-tarjetas" translate="no">'
    '<div class="tb-tarjeta" style="grid-column: 1 / -1;">'
    '<span class="tb-etiqueta">Uso de tus ingresos</span>'
    f"{uso}"
    "</div>"
    "</div>",
    unsafe_allow_html=True,
)

# ---------- Pestañas ----------
tab_resumen, tab_movimientos = st.tabs(["Resumen", "Movimientos"])

with tab_resumen:
    col_izq, col_der = st.columns(2)

    with col_izq:
        st.subheader("Gastos por categoría")
        gastos_filtrados = gastos_cat[gastos_cat.index.isin(categorias)]
        if gastos_filtrados.empty:
            st.info("No hay gastos en este mes para las categorías elegidas.")
        else:
            st.bar_chart(gastos_filtrados.rename("Gastos"), color="#0f766e")

    with col_der:
        st.subheader("Gasto acumulado del mes")
        inicio = pd.Timestamp(mes + "-01")
        fin = inicio + pd.offsets.MonthEnd(0)
        dias = pd.date_range(inicio, fin)
        gasto_por_dia = (
            df_mes[df_mes["tipo"] == "gasto"]
            .groupby("fecha")["monto"]
            .sum()
            .reindex(dias, fill_value=0)
        )
        acumulado = gasto_por_dia.cumsum()
        if es_actual:
            hoy = pd.Timestamp.today().normalize()
            acumulado = acumulado[acumulado.index <= hoy]
        grafico = pd.DataFrame(
            {"Gasto acumulado": acumulado, "Ingresos del mes": ingresos}
        )
        st.line_chart(grafico, color=["#dc2626", "#059669"])

    st.subheader("Ingresos y gastos por mes")
    por_mes = df.pivot_table(
        index="mes", columns="tipo", values="monto", aggfunc="sum", fill_value=0
    )
    por_mes = por_mes.reindex(columns=["ingreso", "gasto"], fill_value=0).tail(12)
    por_mes.columns = ["Ingresos", "Gastos"]
    st.bar_chart(por_mes, color=["#059669", "#dc2626"])

    st.subheader("Mayores gastos del mes")
    grandes = df_mes[df_mes["tipo"] == "gasto"].sort_values("monto", ascending=False).head(5)
    if grandes.empty:
        st.info("No hay gastos en este mes.")
    else:
        tabla_grandes = grandes[["fecha", "descripcion", "categoria", "monto"]].copy()
        tabla_grandes["fecha"] = tabla_grandes["fecha"].dt.strftime("%Y-%m-%d")
        st.dataframe(
            tabla_grandes,
            hide_index=True,
            column_config={
                "fecha": "Fecha",
                "descripcion": "Descripción",
                "categoria": "Categoría",
                "monto": st.column_config.NumberColumn("Monto", format="$ %.2f"),
            },
        )

with tab_movimientos:
    todos = st.checkbox("Mostrar todos los meses", value=False)
    tipo_elegido = st.radio("Tipo", ["Todos", "Ingresos", "Gastos"], horizontal=True)

    base = df if todos else df_mes
    filtrado = base[base["categoria"].isin(categorias)]
    if tipo_elegido == "Ingresos":
        filtrado = filtrado[filtrado["tipo"] == "ingreso"]
    elif tipo_elegido == "Gastos":
        filtrado = filtrado[filtrado["tipo"] == "gasto"]

    tabla = filtrado[["fecha", "tipo", "descripcion", "categoria", "monto"]].copy()
    tabla["fecha"] = tabla["fecha"].dt.strftime("%Y-%m-%d")

    st.caption(f"{len(tabla)} movimientos")
    st.dataframe(
        tabla,
        hide_index=True,
        column_config={
            "fecha": "Fecha",
            "tipo": "Tipo",
            "descripcion": "Descripción",
            "categoria": "Categoría",
            "monto": st.column_config.NumberColumn("Monto", format="$ %.2f"),
        },
    )
    
    exportar = tabla.rename(
        columns={
            "fecha": "Fecha",
            "tipo": "Tipo",
            "descripcion": "Descripción",
            "categoria": "Categoría",
            "monto": "Monto",
        }
    )
    exportar["Tipo"] = exportar["Tipo"].str.capitalize()
    csv = exportar.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")

    st.download_button(
        "Descargar CSV",
        csv,
        file_name="movimientos.csv",
        mime="text/csv",
    )