# Importar librería para conectar Python con Google Sheets
import gspread 


# Función para obtener datos desde Google Sheets
def obtener_datos():

    # Autenticación mediante credenciales de Google Cloud
    cliente = gspread.service_account(
        filename="credenciales.json"
    )

    # Abrir la hoja de cálculo
    archivo = cliente.open("BD_Ventas")

    # Seleccionar la primera hoja
    hoja = archivo.sheet1

    # Leer todos los registros
    datos = hoja.get_all_records()

    # Retornar información obtenida
    return datos