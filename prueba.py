import pyodbc
import secrets
from flask import Flask, jsonify , request, render_template
from validaciones import *
from datetime import datetime, timedelta




cnxn = pyodbc.connect('DRIVER=' + driver + ';SERVER=' + server + ';DATABASE=' + database + ';UID=' + username + ';PWD=' + password)

app = Flask(__name__)

@app.route('/')
def bienvenida():
    
    return jsonify({'mensaje': 'Bienvenido a nuestro api'}), 200


def obtener_clave_secreta():
    token = request.headers.get('Authorization')
    token = token[7:500]  # Eliminar el prefijo 'Bearer '
    cursor = cnxn.cursor()
    cursor.execute("SELECT token, fecha FROM token(nolock) WHERE token=?", token)
    row = cursor.fetchone()
    if row and row[0] == token:  # Comprobar que el token de la base de datos coincide con el enviado en la solicitud
        return str(row[1])  # Devolver la fecha de creación del token como clave secreta
    else:
        return b'clave_secreta_predeterminada'  # Devolver una clave secreta predeterminada

@app.route('/token', methods=['GET'])
def crearToken():
    token = secrets.token_hex(32)

    fecha = datetime.now()

    estado = 1

    # Inserta el token en la tabla 'Tokens'
    cursor = cnxn.cursor()
    cursor.execute("INSERT INTO token (token,fecha,estado) VALUES (?,?,?)", (token,fecha,estado))
    cnxn.commit()


    return jsonify({'Token generado correctamente': 200}), 200


@app.route('/cursos', methods=['GET'])
def listar_cursos():
    try:
        clave_secreta = obtener_clave_secreta()
        if isinstance(clave_secreta, str):  # Si la clave secreta es una cadena, es la fecha de creación del token
            # Verificar si el token tiene menos de 24 horas de creación
            fecha_creacion = datetime.fromisoformat(clave_secreta)
            fecha_actual = datetime.now()
            if fecha_actual - fecha_creacion > timedelta(hours=24):
                #Agregar update para cambiar el estado del token de 1 a 0 en la tabla de sql.
                return jsonify({'mensaje': "Token expirado.", 'code': 401}), 401
        else:  # Si la clave secreta es una cadena de bytes, es una clave secreta predeterminada
            return jsonify({'mensaje': "Error, token inválido.", 'code': 401}), 401

        # Obtener el número de página de la consulta
        pagina = request.args.get('page', default=1, type=int)
        cantidad_reg = 50
        cant_muestra = (pagina - 1) * cantidad_reg

        # Ejecutar la consulta SQL con paginación
        cursor = cnxn.cursor()
        sql = f"SELECT codigo, descripcion, creditos, COUNT(*) OVER() AS total_cursos FROM cursos ORDER BY descripcion ASC OFFSET {cant_muestra} ROWS FETCH NEXT {cantidad_reg} ROWS ONLY"
        cursor.execute(sql)
        datos = cursor.fetchall()
        cursos = []
        total_cursos = 0
        for fila in datos:
            curso = {'codigo': fila[0], 'descripcion': fila[1], 'creditos': fila[2]}
            cursos.append(curso)
            total_cursos = fila[3]  # Obtener el total de cursos del resultado

        respuesta = {'cursos': cursos}
        return jsonify({'total_cursos': total_cursos, 'pagina': pagina,'code': 200 }, respuesta)
    except Exception as ex:
        return jsonify({'mensaje': "Error, no se proporcionó token", 'code': 401}), 401
    

@app.route('/cursos', methods=['POST'])
def registrar_curso():

    print(request.json)
    #if (validar_codigo(request.json['codigo']) and validar_nombre(request.json['nombre']) and validar_creditos(request.json['creditos'])):
    try:
        clave_secreta = obtener_clave_secreta()
        if isinstance(clave_secreta, str):  # Si la clave secreta es una cadena, es la fecha de creación del token
            # Verificar si el token tiene menos de 24 horas de creación
            fecha_creacion = datetime.fromisoformat(clave_secreta)
            fecha_actual = datetime.now()
            if fecha_actual - fecha_creacion > timedelta(hours=24):

                return jsonify({'mensaje': "Token expirado.", 'code': 401}), 401
        else:  # Si la clave secreta es una cadena de bytes, es una clave secreta predeterminada
            return jsonify({'mensaje': "Error, token inválido.", 'code': 401}), 401


        curso = leer_curso_bd(request.json['codigo'])
        if curso != None:
            return jsonify({'mensaje': "Código ya existe, no se puede duplicar.", 'exito': False})
        else:
            cursor = cnxn.cursor()
            sql = """INSERT INTO cursos (codigo, descripcion, creditos) 
            VALUES ('{0}', '{1}', {2})""".format(request.json['codigo'], request.json['descripcion'], request.json['creditos'])
            cursor.execute(sql)
            cnxn.cursor()  # Confirma la acción de inserción.
            return jsonify({'mensaje': "Curso registrado.", 'exito': True})
    except Exception as ex:
            return jsonify({'mensaje': "Error, no se proporciono token",'code': 401}), 401
    #else:
        #return jsonify({'mensaje': "Parámetros inválidos...", 'exito': False})
        #return jsonify({})

def leer_curso_bd(codigo):
    try:
        cursor = cnxn.cursor()
        sql = "SELECT codigo, descripcion, creditos FROM cursos(nolock) WHERE codigo = '{0}'".format(codigo)
        cursor.execute(sql)
        datos = cursor.fetchone()
        if datos != None:
            curso = {'codigo': datos[0], 'descripcion': datos[1], 'creditos': datos[2]}
            return curso
        else:
            return None
    except Exception as ex:
        raise ex




@app.route('/cursos/<codigo>', methods=['GET'])
def leer_curso(codigo):
    try:
        clave_secreta = obtener_clave_secreta()
        if isinstance(clave_secreta, str):  # Si la clave secreta es una cadena, es la fecha de creación del token
            # Verificar si el token tiene menos de 24 horas de creación
            fecha_creacion = datetime.fromisoformat(clave_secreta)
            fecha_actual = datetime.now()
            if fecha_actual - fecha_creacion > timedelta(hours=24):

                # Actualizar el estado del token en la base de datos
                cursor = cnxn.cursor()
                sql = "UPDATE token SET estado = 0 WHERE token = ?"
                result = cursor.execute(sql, (clave_secreta,))
                imp=(result.rowcount)  # Imprime el número de filas actualizadas
                cnxn.commit()

                return jsonify({'mensaje': "Token expirado.", 'code': 401}, imp), 401
        else:  # Si la clave secreta es una cadena de bytes, es una clave secreta predeterminada
            return jsonify({'mensaje': "Error, token inválido.", 'code': 401}), 401
        curso = leer_curso_bd(codigo)
        if curso != None:
            return jsonify({'code': 200, 'curso': curso})
        else:
            return jsonify({'mensaje': "Curso no encontrado.", 'exito': False})
    except Exception as ex:
        return jsonify({'mensaje': "Error, no se proporciono token", 'code': 401}), 401




@app.route('/cursos/<codigo>', methods=['DELETE'])
def eliminar_curso(codigo):
    try:
        clave_secreta = obtener_clave_secreta()
        if isinstance(clave_secreta, str):  # Si la clave secreta es una cadena, es la fecha de creación del token
            # Verificar si el token tiene menos de 24 horas de creación
            fecha_creacion = datetime.fromisoformat(clave_secreta)
            fecha_actual = datetime.now()
            if fecha_actual - fecha_creacion > timedelta(hours=24):

                return jsonify({'mensaje': "Token expirado.", 'code': 401}), 401
        else:  # Si la clave secreta es una cadena de bytes, es una clave secreta predeterminada
            return jsonify({'mensaje': "Error, token inválido.", 'code': 401}), 401

        curso = leer_curso_bd(codigo)
        if curso != None:
            cursor = cnxn.cursor()
            sql = "DELETE FROM cursos WHERE codigo = '{0}'".format(codigo)
            cursor.execute(sql)
            cnxn.cursor()  # Confirma la acción de eliminación.
            return jsonify({'mensaje': "Curso eliminado.", 'exito': True})
        else:
            return jsonify({'mensaje': "Curso no encontrado.", 'exito': False})
    except Exception as ex:
        return jsonify({'mensaje': "Error, no se proporciono token o token invalido"}), 401


@app.route('/cursos/<codigo>', methods=['PUT'])
def actualizar_curso(codigo):
    #if (validar_codigo(codigo) and validar_nombre(request.json['nombre']) and validar_creditos(request.json['creditos'])):
        try:
            clave_secreta = obtener_clave_secreta()
            if isinstance(clave_secreta, str):  # Si la clave secreta es una cadena, es la fecha de creación del token
            # Verificar si el token tiene menos de 24 horas de creación
                fecha_creacion = datetime.fromisoformat(clave_secreta)
                fecha_actual = datetime.now()
                if fecha_actual - fecha_creacion > timedelta(hours=24):

                    return jsonify({'mensaje': "Token expirado.", 'code': 401}), 401
            else:  # Si la clave secreta es una cadena de bytes, es una clave secreta predeterminada
                return jsonify({'mensaje': "Error, token inválido.", 'code': 401}), 401

            curso = leer_curso_bd(codigo)
            if curso != None:
                cursor = cnxn.cursor()
                sql = """UPDATE cursos SET descripcion = '{0}', creditos = {1} 
                WHERE codigo = '{2}'""".format(request.json['descripcion'], request.json['creditos'], codigo)
                cursor.execute(sql)
                cnxn.cursor()  # Confirma la acción de actualización.
                return jsonify({'mensaje': "Curso actualizado.", 'exito': True})
            else:
                return jsonify({'mensaje': "Curso no encontrado.", 'exito': False})
        except Exception as ex:
            return jsonify({'mensaje': "Error", 'exito': False})


def pagina_no_encontrada(error):
    return "<h1>Página no encontrada, metedo no disponible</h1>", 404
if __name__ == '__main__':
    app.register_error_handler(404, pagina_no_encontrada)
    app.run(debug=True,port=5000)