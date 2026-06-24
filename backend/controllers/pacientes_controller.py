from controllers.common import (
    api_error,
    api_ok,
    insert_dynamic,
    request_data,
    row_to_dict,
    rows_to_dicts,
    update_dynamic,
)
from database import get_db_connection


SIGNOS_VITALES = {
    "temperatura",
    "presion",
    "presion_arterial",
    "frecuencia_cardiaca",
    "frecuencia_respiratoria",
    "peso",
    "talla",
}


def _normalizar_paciente(datos):
    return {
        "nombre": datos.get("nombre") or datos.get("nombres"),
        "apellidos": datos.get("apellidos"),
        "curp": (datos.get("curp") or "").upper(),
        "fecha_nac": datos.get("fecha_nac") or datos.get("fechaNac"),
        "sexo": datos.get("sexo"),
        "telefono": datos.get("telefono"),
        "correo": datos.get("correo"),
        "direccion": datos.get("direccion"),
        "tipo_sangre": datos.get("tipo_sangre") or datos.get("tipoSangre"),
        "alergias": datos.get("alergias"),
        "enf_cronicas": datos.get("enf_cronicas") or datos.get("enfCronicas"),
        "contacto_emergencia": datos.get("contacto_emergencia") or datos.get("contactoEme"),
        "estado": datos.get("estado", "Activo"),
    }


def crear_paciente():
    datos = request_data()
    paciente = _normalizar_paciente(datos)
    obligatorios = ["nombre", "apellidos", "curp", "fecha_nac", "sexo", "telefono", "direccion"]
    faltantes = [campo for campo in obligatorios if not paciente.get(campo)]
    if faltantes:
        return api_error("Campos obligatorios faltantes: " + ", ".join(faltantes), 400)

    conexion = get_db_connection()
    if not conexion:
        return api_error("Error de conexion a la base de datos", 500)

    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT id_paciente FROM paciente WHERE curp = %s", (paciente["curp"],))
        if cursor.fetchone():
            return api_error("La CURP ingresada ya se encuentra registrada.", 400)

        insert_dynamic(cursor, "paciente", paciente)
        conexion.commit()
        nuevo_id = cursor.lastrowid
        return api_ok({"mensaje": "Paciente registrado con exito.", "id_paciente": f"PAC-{nuevo_id:04d}"}, 201)
    except Exception as exc:
        conexion.rollback()
        return api_error(str(exc), 500)
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()


def buscar_pacientes():
    criterio = request_data().get("criterio") or ""
    conexion = get_db_connection()
    if not conexion:
        return api_error("Error de conexion a la base de datos", 500)

    try:
        from flask import request

        criterio = request.args.get("q") or request.args.get("criterio") or criterio
        like = f"%{criterio}%"
        criterio_id = criterio.split("-")[-1] if criterio.upper().startswith("PAC-") else criterio
        es_id = str(criterio_id).isdigit()

        cursor = conexion.cursor()
        params = [like, like, like]
        id_filter = ""
        if es_id:
            id_filter = "OR id_paciente = %s"
            params.append(int(criterio_id))

        cursor.execute(
            f"""
            SELECT *
            FROM paciente
            WHERE (nombre LIKE %s OR apellidos LIKE %s OR curp LIKE %s {id_filter})
              AND COALESCE(estado, 'Activo') <> 'Inactivo'
            ORDER BY apellidos, nombre
            """,
            tuple(params),
        )
        pacientes = rows_to_dicts(cursor, cursor.fetchall())
        if not pacientes:
            return api_error("Error: Paciente no encontrado en el sistema.", 404, "MSG-02")
        return api_ok({"pacientes": pacientes})
    except Exception as exc:
        return api_error(str(exc), 500)
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()


def obtener_paciente(id):
    conexion = get_db_connection()
    if not conexion:
        return api_error("Error de conexion a la base de datos", 500)

    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM paciente WHERE id_paciente = %s", (id,))
        paciente = row_to_dict(cursor, cursor.fetchone())
        if not paciente:
            return api_error("Paciente no encontrado.", 404, "ERR-01")

        cursor.execute("SELECT * FROM cita WHERE id_paciente = %s ORDER BY fecha DESC, hora DESC", (id,))
        citas = rows_to_dicts(cursor, cursor.fetchall())
        return api_ok({"paciente": paciente, "citas": citas})
    except Exception as exc:
        return api_error(str(exc), 500)
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()


def actualizar_paciente(id):
    datos = request_data()
    if SIGNOS_VITALES.intersection(datos.keys()):
        return api_error("Acceso denegado: La modificacion de signos vitales es exclusiva de enfermeria.", 403, "ERR-05")

    paciente = _normalizar_paciente(datos)
    paciente.pop("estado", None)

    conexion = get_db_connection()
    if not conexion:
        return api_error("Error de conexion a la base de datos", 500)

    try:
        cursor = conexion.cursor()
        update_dynamic(cursor, "paciente", "id_paciente", id, paciente)
        conexion.commit()
        return api_ok({"mensaje": "Paciente actualizado."})
    except Exception as exc:
        conexion.rollback()
        return api_error(str(exc), 500)
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()


def cancelar_paciente(id):
    conexion = get_db_connection()
    if not conexion:
        return api_error("Error de conexion a la base de datos", 500)

    try:
        cursor = conexion.cursor()
        update_dynamic(cursor, "paciente", "id_paciente", id, {"estado": "Inactivo"})
        conexion.commit()
        return api_ok({"mensaje": "El registro ha sido cancelado y actualizado correctamente en el historial.", "codigo": "RN-02"})
    except Exception as exc:
        conexion.rollback()
        return api_error(str(exc), 500)
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()
