from flask import jsonify

from controllers.common import api_error, api_ok, insert_dynamic, request_data, rows_to_dicts, row_to_dict, update_dynamic
from database import get_db_connection


def obtener_medicos():
    conexion = get_db_connection()
    if not conexion:
        return api_error("Error de conexion a la base de datos", 500)

    try:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT * FROM medico
            WHERE COALESCE(estado, 'Activo') <> 'Inactivo'
            ORDER BY apellidos, nombre
            """
        )
        return api_ok({"medicos": rows_to_dicts(cursor, cursor.fetchall())})
    except Exception as exc:
        return api_error(str(exc), 500)
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()


def obtener_medico(id):
    conexion = get_db_connection()
    if not conexion:
        return api_error("Error de conexion a la base de datos", 500)

    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM medico WHERE id_medico = %s", (id,))
        medico = row_to_dict(cursor, cursor.fetchone())
        if not medico:
            return api_error("Medico no encontrado.", 404)
        return api_ok({"medico": medico})
    except Exception as exc:
        return api_error(str(exc), 500)
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()


def crear_medico(data=None):
    data = data or request_data()
    required = ["nombre", "apellidos", "especialidad", "cedula"]
    missing = [field for field in required if not data.get(field)]
    if missing:
        return api_error("Campos obligatorios faltantes: " + ", ".join(missing), 400)

    conexion = get_db_connection()
    if not conexion:
        return api_error("Error de conexion a la base de datos", 500)

    try:
        cursor = conexion.cursor()
        insert_dynamic(
            cursor,
            "medico",
            {
                "nombre": data.get("nombre"),
                "apellidos": data.get("apellidos"),
                "especialidad": data.get("especialidad"),
                "cedula": data.get("cedula"),
                "correo": data.get("correo"),
                "telefono": data.get("telefono"),
                "estado": data.get("estado", "Activo"),
            },
        )
        conexion.commit()
        return jsonify({"mensaje": "Medico registrado.", "id_medico": cursor.lastrowid}), 201
    except Exception as exc:
        conexion.rollback()
        return api_error(str(exc), 500)
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()


def actualizar_medico(id, data=None):
    data = data or request_data()
    conexion = get_db_connection()
    if not conexion:
        return api_error("Error de conexion a la base de datos", 500)

    try:
        cursor = conexion.cursor()
        update_dynamic(
            cursor,
            "medico",
            "id_medico",
            id,
            {
                "nombre": data.get("nombre"),
                "apellidos": data.get("apellidos"),
                "especialidad": data.get("especialidad"),
                "cedula": data.get("cedula"),
                "correo": data.get("correo"),
                "telefono": data.get("telefono"),
                "estado": data.get("estado"),
            },
        )
        conexion.commit()
        return api_ok({"mensaje": "Medico actualizado."})
    except Exception as exc:
        conexion.rollback()
        return api_error(str(exc), 500)
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()


def eliminar_medico(id):
    conexion = get_db_connection()
    if not conexion:
        return api_error("Error de conexion a la base de datos", 500)

    try:
        cursor = conexion.cursor()
        update_dynamic(cursor, "medico", "id_medico", id, {"estado": "Inactivo"})
        conexion.commit()
        return api_ok({"mensaje": "Medico desactivado sin eliminacion fisica.", "codigo": "RN-02"})
    except Exception as exc:
        conexion.rollback()
        return api_error(str(exc), 500)
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()
