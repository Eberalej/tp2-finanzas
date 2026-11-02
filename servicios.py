import requests

URL_BASE = "https://dolarapi.com/v1/dolares/"


def obtener_dolar(tipo):
    """Pide la cotización a DolarAPI. tipo: 'oficial' o 'blue'.
    Devuelve un diccionario con compra y venta, o None si algo falla."""
    try:
        respuesta = requests.get(URL_BASE + tipo, timeout=5)
        respuesta.raise_for_status()
        datos = respuesta.json()
        return {
            "compra": float(datos["compra"]),
            "venta": float(datos["venta"]),
            "fecha": datos.get("fechaActualizacion", ""),
            "fuente": "DolarAPI",
        }
    except requests.exceptions.Timeout:
        print("DolarAPI tardó demasiado en responder")
        return None
    except (requests.exceptions.RequestException, KeyError, ValueError, TypeError):
        print("No se pudo obtener la cotización de DolarAPI")
        return None

URL_BCRA = "https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/5"


def obtener_oficial_bcra():
    """Pide al BCRA el último tipo de cambio mayorista (A 3500).
    Devuelve un diccionario o None si algo falla."""
    try:
        respuesta = requests.get(URL_BCRA, timeout=8)
        respuesta.raise_for_status()
        datos = respuesta.json()
        detalle = datos["results"][0]["detalle"]
        ultimo = max(detalle, key=lambda registro: registro["fecha"])
        return {
            "compra": None,
            "venta": float(ultimo["valor"]),
            "fecha": ultimo["fecha"],
            "fuente": "BCRA (mayorista A 3500)",
        }
    except requests.exceptions.Timeout:
        print("El BCRA tardó demasiado en responder")
        return None
    except (requests.exceptions.RequestException, KeyError, IndexError, ValueError, TypeError):
        print("No se pudo obtener la cotización del BCRA")
        return None


def obtener_oficial():
    """Dólar oficial: primero DolarAPI y, si falla, el BCRA como respaldo."""
    cotizacion = obtener_dolar("oficial")
    if cotizacion is None:
        cotizacion = obtener_oficial_bcra()
    return cotizacion