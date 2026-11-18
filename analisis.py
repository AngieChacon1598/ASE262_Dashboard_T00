
from datetime import date, datetime
from math import isfinite
from unicodedata import combining, normalize

from conexion_sheets import obtener_datos


# =====================================================
# CONFIGURACIÓN
# =====================================================

ESTADO_COMPLETADA = "completada"

# True: ejecuta datos de prueba.
# False: obtiene los datos reales de Google Sheets.
MODO_PRUEBA = False


# =====================================================
# 1. FUNCIONES DE CONVERSIÓN Y NORMALIZACIÓN
# =====================================================
def normalizar_texto(valor):
    texto = normalize("NFKD", str(valor or "").strip().casefold())
    return "".join(
        caracter for caracter in texto
        if not combining(caracter)
    )


def fecha_a_date(valor):
    if isinstance(valor, datetime):
        return valor.date()

    if isinstance(valor, date):
        return valor

    if valor is None:
        return None

    texto = str(valor).strip()

    if not texto:
        return None

    for formato in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(texto).date()
    except ValueError:
        return None


def numero_a_float(valor):

    if isinstance(valor, bool):
        raise ValueError("No se permiten valores booleanos.")

    if isinstance(valor, (int, float)):
        numero = float(valor)

    else:
        texto = str(valor or "").strip()
        texto = texto.replace("S/", "").replace(" ", "")

        if not texto:
            raise ValueError("El valor numérico está vacío.")

        if "," in texto and "." in texto:

            if texto.rfind(",") > texto.rfind("."):
                texto = texto.replace(".", "").replace(",", ".")
            else:
                texto = texto.replace(",", "")

        elif "," in texto:

            parte_decimal = texto.rsplit(",", 1)[1]

            if len(parte_decimal) <= 2:
                texto = texto.replace(",", ".")
            else:
                texto = texto.replace(",", "")

        try:
            numero = float(texto)

        except (ValueError, TypeError):
            raise ValueError(f"Valor numérico incorrecto: {valor!r}")

    if not isfinite(numero):
        raise ValueError(f"El número debe ser finito: {valor!r}")

    return numero


def cantidad_registro(registro):

    cantidad = numero_a_float(registro.get("Cantidad"))

    if not cantidad.is_integer():
        raise ValueError("La cantidad debe ser un número entero.")

    return int(cantidad)


def importe_registro(registro):

    cantidad = cantidad_registro(registro)
    precio = numero_a_float(registro.get("Precio"))

    if cantidad < 0:
        raise ValueError("La cantidad no puede ser negativa.")

    if precio < 0:
        raise ValueError("El precio no puede ser negativo.")

    return cantidad * precio


# =====================================================
# 2. VALIDACIÓN DE REGISTROS
# =====================================================

def validar_registro(registro):

    if not isinstance(registro, dict):
        raise TypeError("El registro debe ser un diccionario.")

    campos_obligatorios = [
        "Producto",
        "Cantidad",
        "Precio",
        "Estado_Venta"
    ]

    # Comprobar campos obligatorios
    for campo in campos_obligatorios:

        if campo not in registro:
            raise KeyError(f"Falta el campo: {campo}")

        if registro[campo] is None or str(registro[campo]).strip() == "":
            raise ValueError(f"El campo {campo} está vacío.")

    # Validar producto
    if not str(registro["Producto"]).strip():
        raise ValueError("El producto no es válido.")

    # Validar cantidad
    cantidad = cantidad_registro(registro)

    if cantidad <= 0:
        raise ValueError("La cantidad debe ser mayor que cero.")

    # Validar precio
    precio = numero_a_float(registro["Precio"])

    if precio < 0:
        raise ValueError("El precio no puede ser negativo.")

    # Validar estado
    if not normalizar_texto(registro["Estado_Venta"]):
        raise ValueError("El estado de venta no es válido.")

    # Validar fecha cuando existe
    fecha = registro.get("Fecha")

    if fecha is not None and str(fecha).strip():

        if fecha_a_date(fecha) is None:
            raise ValueError(f"Fecha incorrecta: {fecha}")

    return True


def validar_registros(registros):

    if registros is None:
        raise ValueError("No se recibieron datos.")

    if not isinstance(registros, list):
        raise TypeError("Los registros deben estar en una lista.")

    registros_validos = []
    errores = []

    for numero, registro in enumerate(registros, start=2):

        try:
            validar_registro(registro)
            registros_validos.append(registro)

        except (KeyError, ValueError, TypeError, AttributeError) as error:

            mensaje = f"Fila {numero}: {error}"
            errores.append(mensaje)

    return registros_validos, errores


# =====================================================
# 3. FUNCIONES DE ANÁLISIS COMERCIAL
# =====================================================

def contar_registros(registros):

    if registros is None:
        raise ValueError("No existen registros para contar.")

    return len(registros)


def agrupar_por_producto(registros, solo_completadas=False):

    resumen = {}

    for registro in registros:

        if solo_completadas and not es_estado(
            registro, ESTADO_COMPLETADA
        ):
            continue

        producto = str(registro.get("Producto") or "Sin producto")

        cantidad = cantidad_registro(registro)

        resumen[producto] = resumen.get(producto, 0) + cantidad

    return resumen


def calcular_ventas(registros):

    if registros is None:
        raise ValueError("No se recibieron datos para calcular ventas.")

    total = 0

    for registro in registros:
        total += importe_registro(registro)

    return total


def es_estado(registro, estado):

    return normalizar_texto(
        registro.get("Estado_Venta")
    ) == estado


def _ventas_por_campo(registros, campo, solo_completadas=False):

    resumen = {}

    for registro in registros:

        if solo_completadas and not es_estado(
            registro, ESTADO_COMPLETADA
        ):
            continue

        clave = str(registro.get(campo) or "Sin dato")

        venta = importe_registro(registro)

        resumen[clave] = resumen.get(clave, 0) + venta

    return resumen


def ventas_por_producto(registros, solo_completadas=True):

    return _ventas_por_campo(
        registros, "Producto", solo_completadas
    )


def ventas_por_vendedor(registros, solo_completadas=False):

    return _ventas_por_campo(
        registros, "Vendedor", solo_completadas
    )


def ventas_por_categoria(registros, solo_completadas=False):

    return _ventas_por_campo(
        registros, "Categoria", solo_completadas
    )


def ventas_por_canal(registros, solo_completadas=False):

    return _ventas_por_campo(
        registros, "Canal_Venta", solo_completadas
    )


def ventas_por_ciudad(registros, solo_completadas=False):

    return _ventas_por_campo(
        registros, "Ciudad", solo_completadas
    )


def ventas_por_region(registros, solo_completadas=False):

    return _ventas_por_campo(
        registros, "Region", solo_completadas
    )


def ventas_por_estado(registros):

    return _ventas_por_campo(
        registros, "Estado_Venta"
    )


def ventas_por_fecha(registros, solo_completadas=False):

    resumen = {}

    for registro in registros:

        if solo_completadas and not es_estado(
            registro, ESTADO_COMPLETADA
        ):
            continue

        fecha = fecha_a_date(registro.get("Fecha"))

        if fecha is None:
            continue

        clave = fecha.isoformat()

        venta = importe_registro(registro)

        resumen[clave] = resumen.get(clave, 0) + venta

    return resumen


def contar_ventas_por_estado(registros):

    resumen = {}

    for registro in registros:

        estado = str(
            registro.get("Estado_Venta") or "Sin estado"
        )

        resumen[estado] = resumen.get(estado, 0) + 1

    return resumen


# =====================================================
# 4. RESUMEN GENERAL DEL DASHBOARD
# =====================================================

def resumen_comercial(registros):

    if registros is None:
        raise ValueError("No existen datos para elaborar el resumen.")

    completadas = [
        registro for registro in registros
        if es_estado(registro, ESTADO_COMPLETADA)
    ]

    unidades_por_producto = agrupar_por_producto(completadas)

    operaciones_completadas = len(completadas)

    ingresos_completados = calcular_ventas(completadas)

    return {
        "unidades_completadas": sum(
            unidades_por_producto.values()
        ),

        "ingresos_completados": ingresos_completados,

        "ticket_promedio": (
            ingresos_completados / operaciones_completadas
            if operaciones_completadas > 0
            else 0
        )
    }


# =====================================================
# 5. DATOS DE PRUEBA
# =====================================================

datos_prueba = [

    # Registro correcto
    {
        "Producto": "Laptop",
        "Cantidad": 2,
        "Precio": 2500,
        "Vendedor": "Juan",
        "Categoria": "Tecnología",
        "Canal_Venta": "Online",
        "Ciudad": "Lima",
        "Region": "Costa",
        "Estado_Venta": "Completada",
        "Fecha": "2026-11-17"
    },

    # Registro incorrecto: cantidad no numérica
    {
        "Producto": "Mouse",
        "Cantidad": "ABC",
        "Precio": 50,
        "Vendedor": "Ana",
        "Categoria": "Accesorios",
        "Canal_Venta": "Presencial",
        "Ciudad": "Cañete",
        "Region": "Costa",
        "Estado_Venta": "Completada",
        "Fecha": "2026-11-17"
    },

    # Registro incorrecto: precio negativo
    {
        "Producto": "Teclado",
        "Cantidad": 3,
        "Precio": -100,
        "Vendedor": "Pedro",
        "Categoria": "Accesorios",
        "Canal_Venta": "Online",
        "Ciudad": "Lima",
        "Region": "Costa",
        "Estado_Venta": "Pendiente",
        "Fecha": "2026-11-17"
    },

    # Registro incorrecto: producto vacío
    {
        "Producto": "",
        "Cantidad": 4,
        "Precio": 80,
        "Vendedor": "Luis",
        "Categoria": "Accesorios",
        "Canal_Venta": "Tienda",
        "Ciudad": "Ica",
        "Region": "Costa",
        "Estado_Venta": "Completada",
        "Fecha": "2026-11-17"
    },

    # Registro correcto
    {
        "Producto": "Monitor",
        "Cantidad": 2,
        "Precio": 800,
        "Vendedor": "Ana",
        "Categoria": "Tecnología",
        "Canal_Venta": "Tienda",
        "Ciudad": "Chincha",
        "Region": "Costa",
        "Estado_Venta": "Completada",
        "Fecha": "2026-11-17"
    }
]


# =====================================================
# 6. EJECUCIÓN Y PRUEBAS
# =====================================================

if __name__ == "__main__":

    try:

        print("\n===================================")
        print("       DASHBOARD ANALÍTICO")
        print("===================================")

        # Seleccionar origen de datos
        if MODO_PRUEBA:

            print("\nMODO: DATOS DE PRUEBA")
            datos = datos_prueba

        else:

            print("\nMODO: GOOGLE SHEETS")
            datos = obtener_datos()

        # Validar los registros
        datos_validos, errores = validar_registros(datos)

        print("\n===== VALIDACIÓN DE DATOS =====")

        print("Registros recibidos:", len(datos))
        print("Registros válidos:", len(datos_validos))
        print("Registros rechazados:", len(errores))

        # Mostrar errores encontrados
        for error in errores:
            print("ERROR:", error)

        # Comprobar que existan datos válidos
        if not datos_validos:
            raise ValueError(
                "No existen registros válidos para procesar."
            )

        # Procesamiento de datos
        resumen = resumen_comercial(datos_validos)

        print("\n===== RESULTADOS COMERCIALES =====")

        print("Total de registros:", contar_registros(datos_validos))

        print(
            "Unidades completadas:",
            resumen["unidades_completadas"]
        )

        print(
            "Ingresos completados S/:",
            f"{resumen['ingresos_completados']:,.2f}"
        )

        print(
            "Ticket promedio S/:",
            f"{resumen['ticket_promedio']:,.2f}"
        )

        print(
            "\nVentas por producto:",
            ventas_por_producto(datos_validos)
        )

        print(
            "Ventas por vendedor:",
            ventas_por_vendedor(datos_validos, True)
        )

        print(
            "Ventas por categoría:",
            ventas_por_categoria(datos_validos, True)
        )

        print(
            "Ventas por canal:",
            ventas_por_canal(datos_validos, True)
        )

        print(
            "Ventas por ciudad:",
            ventas_por_ciudad(datos_validos, True)
        )

        print(
            "Ventas por región:",
            ventas_por_region(datos_validos, True)
        )

        print(
            "Ventas por estado:",
            ventas_por_estado(datos_validos)
        )

        print(
            "Ventas por fecha:",
            ventas_por_fecha(datos_validos, True)
        )

        print(
            "Cantidad por estado:",
            contar_ventas_por_estado(datos_validos)
        )

        print("\nProcesamiento finalizado correctamente.")

    except ConnectionError as error:

        print("\nERROR DE CONEXIÓN:", error)

    except (ValueError, TypeError, KeyError) as error:

        print("\nERROR DE VALIDACIÓN O PROCESAMIENTO:", error)

    except Exception as error:

        print("\nERROR INESPERADO:", error)
