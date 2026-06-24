from datetime import date

from controllers.common import api_error, api_ok, insert_dynamic, request_data, rows_to_dicts, row_to_dict, update_dynamic
from database import get_db_connection


ESTADOS_OCUPADOS = ("Programada", "Modificada")


def _cita_disponible(cursor, id_medico, fecha, hora, excluir_id=None):
    params = [id_medico, fecha, hora, *ESTADOS_OCUPADOS]
    extra = ""
    if excluir_id:
        extra = "AND id_cita <> %s"
        params.append(excluir_id)
    cursor.execute(
        f"""
        SELECT COUNT(*) FROM cita
        WHERE id_medico = %s
          AND fecha = %s
          AND hora = %s
          AND estado IN (%s, %s)
          {extra}
        """,
        tuple(params),
    )
    return cursor.fetchone()[0] == 0


def obtener_citas():
    conexion = get_db_connection()
    if not conexion:
        return api_error("Error de conexion a la base de datos", 500)

    try:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT c.*, p.nombre AS paciente_nombre, p.apellidos AS paciente_apellidos,
                   m.nombre AS medico_nombre, m.apellidos AS medico_apellidos, m.especialidad
            FROM cita c
            LEFT JOIN paciente p ON p.id_paciente = c.id_paciente
            LEFT JOIN medico m ON m.id_medico = c.id_medico
            ORDER BY c.fecha DESC, c.hora DESC
            """
        )
        return api_ok({"citas": rows_to_dicts(cursor, cursor.fetchall())})
    except Exception as exc:
        return api_error(str(exc), 500)
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()


def obtener_cita(id):
    conexion = get_db_connection()
    if not conexion:
        return api_error("Error de conexion a la base de datos", 500)

    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM cita WHERE id_cita = %s", (id,))
        cita = row_to_dict(cursor, cursor.fetchone())
        if not cita:
            return api_error("Cita no encontrada.", 404)
        return api_ok({"cita": cita})
    except Exception as exc:
        return api_error(str(exc), 500)
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()


def crear_cita(data=None):
    data = data or request_data()
    required = ["id_paciente", "id_medico", "fecha", "hora", "motivo"]
    missing = [field for field in required if not data.get(field)]
    if missing:
        return api_error("Campos obligatorios faltantes: " + ", ".join(missing), 400)

    conexion = get_db_connection()
    if not conexion:
        return api_error("Error de conexion a la base de datos", 500)

    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT id_paciente FROM paciente WHERE id_paciente = %s", (data.get("id_paciente"),))
        if not cursor.fetchone():
            return api_error("Error: El paciente no existe. Proceda a registrar sus datos primero.", 404, "ERR-01")

        if not _cita_disponible(cursor, data.get("id_medico"), data.get("fecha"), data.get("hora")):
            return api_error("Error: El medico no se encuentra disponible en el horario seleccionado.", 409, "MSG-04")

        insert_dynamic(
            cursor,
            "cita",
            {
                "id_paciente": data.get("id_paciente"),
                "id_medico": data.get("id_medico"),
                "fecha": data.get("fecha"),
                "hora": data.get("hora"),
                "motivo": data.get("motivo"),
                "estado": "Programada",
                "reprogramada": 0,
            },
        )
        conexion.commit()
        return api_ok({"mensaje": "Cita registrada.", "id_cita": cursor.lastrowid, "estado": "Programada"}, 201)
    except Exception as exc:
        conexion.rollback()
        return api_error(str(exc), 500)
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()


def actualizar_cita(id, data=None):
    data = data or request_data()
    conexion = get_db_connection()
    if not conexion:
        return api_error("Error de conexion a la base de datos", 500)

    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM cita WHERE id_cita = %s", (id,))
        cita = row_to_dict(cursor, cursor.fetchone())
        if not cita:
            return api_error("Cita no encontrada.", 404)

        nuevo_estado = data.get("estado")
        nueva_fecha = data.get("fecha")
        nueva_hora = data.get("hora")
        nuevo_medico = data.get("id_medico", cita.get("id_medico"))

        if nuevo_estado == "Atendida" and cita.get("estado") == "Cancelada":
            return api_error("Una cita cancelada no puede marcarse como atendida.", 409)

        quiere_reprogramar = bool(nueva_fecha or nueva_hora)
        if quiere_reprogramar:
            if cita.get("estado") == "Modificada" or cita.get("reprogramada"):
                return api_error("Limite alcanzado: Esta cita ya fue reprogramada anteriormente y no admite mas cambios.", 409, "ERR-03")
            fecha_final = nueva_fecha or cita.get("fecha")
            hora_final = nueva_hora or cita.get("hora")
            if not _cita_disponible(cursor, nuevo_medico, fecha_final, hora_final, excluir_id=id):
                return api_error("Aviso: No hay medicos disponibles para la fecha y hora seleccionada.", 409, "ERR-02")
            data["estado"] = "Modificada"
            data["reprogramada"] = 1

        update_dynamic(
            cursor,
            "cita",
            "id_cita",
            id,
            {
                "id_medico": data.get("id_medico"),
                "fecha": data.get("fecha"),
                "hora": data.get("hora"),
                "motivo": data.get("motivo"),
                "estado": data.get("estado"),
                "reprogramada": data.get("reprogramada"),
            },
        )
        conexion.commit()
        return api_ok({"mensaje": "Cita actualizada.", "codigo": "RN-06" if data.get("estado") == "Cancelada" else None})
    except Exception as exc:
        conexion.rollback()
        return api_error(str(exc), 500)
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()


def eliminar_cita(id):
    return actualizar_cita(id, {"estado": "Cancelada"})


def agenda_medicos():
    from flask import request

    data = request_data()
    id_medico = request.args.get("id_medico") or data.get("id_medico")
    fecha = request.args.get("fecha") or data.get("fecha")
    if not id_medico or not fecha:
        return api_error("id_medico y fecha son obligatorios.", 400)

    conexion = get_db_connection()
    if not conexion:
        return api_error("Error de conexion a la base de datos", 500)

    try:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT hora, estado
            FROM cita
            WHERE id_medico = %s AND fecha = %s AND estado IN ('Programada', 'Modificada')
            ORDER BY hora
            """,
            (id_medico, fecha),
        )
        ocupadas = {str(row[0]): row[1] for row in cursor.fetchall()}
        bloques = []
        for hour in range(8, 20):
            for minute in (0, 30):
                slot = f"{hour:02d}:{minute:02d}:00"
                bloques.append({"hora": slot[:5], "estado": "Ocupado" if slot in ocupadas else "Disponible"})
        return api_ok({"fecha": fecha, "id_medico": id_medico, "bloques": bloques})
    except Exception as exc:
        return api_error(str(exc), 500)
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()
