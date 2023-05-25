# Valida el código (si es numérico y de longitud 6).
def validar_codigo(codigo: str) -> bool:
    return (codigo.isnumeric() and len(codigo) == 6)

# Valida el nombre (si es un texto sin espacios en blanco de entre 1 y 30 caracteres).
def validar_nombre(nombre: str) -> bool:
    nombre = nombre.strip()
    return (len(nombre) > 0 and len(nombre) <= 30)

# Valida que los créditos estén entre 1 y 9.
def validar_creditos(creditos: str) -> bool:
    creditos_texto = str(creditos)
    if creditos_texto.isnumeric():
        return (creditos >= 1 and creditos <= 9)
    else:
        return False

import pyodbc

server = 'DESKTOP-F4S0BBC\SQLEXPRESS01'
database = 'api_flask'
username = 'aaa'
password = 'aaa'
driver = '{ODBC Driver 17 for SQL Server}'

def validar_token(token):
    if not token:
        return {"error": "No se proporcionó ningún token."}, 401
    try:
        cnxn = pyodbc.connect('DRIVER=' + driver + ';SERVER=' + server + ';DATABASE=' + database + ';UID=' + username + ';PWD=' + password)
        cursor = cnxn.cursor()
        sql = "SELECT * FROM token WHERE token = ?"
        cursor.execute(sql, token)
        data = cursor.fetchone()
        if data:
            return True
        else:
            return {"error": "Token inválido."}, 401
    except Exception as ex:
        return {"error": "Error en la validación del token."}, 500
