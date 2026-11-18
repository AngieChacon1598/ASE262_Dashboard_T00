import logging
from datetime import datetime

import gspread
from flask import Flask, redirect, render_template, url_for
from google.auth.exceptions import GoogleAuthError
from requests.exceptions import RequestException

from analisis import (
    cantidad_registro,
    numero_a_float,
    resumen_comercial,
)
from conexion_sheets import obtener_datos
from graficos import (
    grafico_barras,
    grafico_canales,
    grafico_cantidad_estados,
    grafico_categorias,
    grafico_ciudades,
    grafico_dona,
    grafico_estados,
    grafico_evolucion_ventas,
    grafico_regiones,
    grafico_vendedores,
)


app = Flask(__name__)
app.logger.setLevel(logging.INFO)

_datos_cache = None
_ultima_actualizacion = None
_ERRORES_FUENTE = (
    gspread.exceptions.GSpreadException,
    GoogleAuthError,
    OSError,
    RequestException,
    ValueError,
)

_GRAFICOS = (
    ("Unidades vendidas por producto", grafico_barras),
    ("Ventas por producto", grafico_dona),
    ("Ventas por vendedor", grafico_vendedores),
    ("Ventas por categoría", grafico_categorias),
    ("Ventas por canal", grafico_canales),
    ("Ventas por ciudad", grafico_ciudades),
    ("Distribución por región", grafico_regiones),
    ("Importe por estado de venta", grafico_estados),
    ("Evolución de ventas", grafico_evolucion_ventas),
    ("Operaciones por estado", grafico_cantidad_estados),
)

_COLUMNAS_REQUERIDAS = (
    "Fecha",
    "Producto",
    "Categoria",
    "Cantidad",
    "Precio",
    "Vendedor",
    "Canal_Venta",
    "Ciudad",
    "Region",
    "Estado_Venta",
)


class ErrorProcesamientoDatos(ValueError):
    pass


def _validar_datos(datos):
    if not isinstance(datos, list):
        raise ErrorProcesamientoDatos("La hoja no devolvió una lista de registros.")
    for numero_fila, registro in enumerate(datos, start=2):
        if not isinstance(registro, dict):
            raise ErrorProcesamientoDatos(f"El registro {numero_fila} tiene un formato inválido.")
        faltantes = [campo for campo in _COLUMNAS_REQUERIDAS if campo not in registro]
        if faltantes:
            raise ErrorProcesamientoDatos(
                f"Faltan columnas requeridas en el registro {numero_fila}."
            )
        try:
            cantidad_registro(registro)
            numero_a_float(registro["Precio"])
        except (TypeError, ValueError, OverflowError) as error:
            raise ErrorProcesamientoDatos(
                f"La cantidad o el precio del registro {numero_fila} no es válido."
            ) from error


def _cargar_datos(forzar_actualizacion=False):
    global _datos_cache, _ultima_actualizacion

    if _datos_cache is not None and not forzar_actualizacion:
        return _datos_cache, None, True

    try:
        nuevos_datos = obtener_datos()
    except _ERRORES_FUENTE:
        app.logger.exception("No se pudieron obtener los datos de Google Sheets.")
        return (
            _datos_cache or [],
            "No fue posible conectar con Google Sheets. Intenta actualizar los datos.",
            False,
        )

    try:
        _validar_datos(nuevos_datos)
    except ErrorProcesamientoDatos as error:
        app.logger.error("No se pudieron procesar los datos de Google Sheets: %s", error)
        return (
            _datos_cache or [],
            "Los datos recibidos contienen columnas o valores inválidos. Revisa la hoja de cálculo.",
            True,
        )

    _datos_cache = nuevos_datos
    _ultima_actualizacion = datetime.now().astimezone()
    return _datos_cache, None, True


def _render_dashboard(datos, error_fuente=None, estado_conexion=True, codigo=200):
    resumen = resumen_comercial(datos)
    graficos = [
        {"titulo": titulo, "html": funcion(datos).to_html(full_html=False, include_plotlyjs=False)}
        for titulo, funcion in _GRAFICOS
    ]

    return (
        render_template(
            "dashboard.html",
            total_registros=len(datos),
            unidades_completadas=resumen["unidades_completadas"],
            ingresos_completados=resumen["ingresos_completados"],
            ticket_promedio=resumen["ticket_promedio"],
            graficos=graficos,
            ultima_actualizacion=(
                _ultima_actualizacion.strftime("%d/%m/%Y %H:%M")
                if _ultima_actualizacion
                else None
            ),
            error_fuente=error_fuente,
            estado_conexion=estado_conexion,
        ),
        codigo,
    )


@app.route("/", methods=["GET"])
def dashboard():
    datos, error_fuente, conectado = _cargar_datos()
    respuesta, codigo = _render_dashboard(
        datos,
        error_fuente=error_fuente,
        estado_conexion=conectado,
        codigo=503 if error_fuente and not conectado else 200,
    )
    return respuesta, codigo


@app.route("/actualizar", methods=["POST"])
def actualizar_datos():
    datos, error_fuente, conectado = _cargar_datos(forzar_actualizacion=True)
    if error_fuente:
        respuesta, codigo = _render_dashboard(
            datos,
            error_fuente=error_fuente,
            estado_conexion=conectado,
            codigo=503 if not conectado and not _datos_cache else 200,
        )
        return respuesta, codigo
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(debug=True)
