import json
from datetime import datetime

from controllers.common import api_error, api_ok, insert_dynamic, request_data, rows_to_dicts, row_to_dict, update_dynamic
from database import get_db_connection


def _days_between(start_date, end_date):
    start = datetime.strptime(str(start_date), "%Y-%m-%d").date()
    end = datetime.strptime(str(end_date), "%Y-%m-%d").date()
    return (end - start).days


def obtener_ordenes():
    conexion = get_db_connection()
    if not conexion:
        return api_error("Error de conexion a la base de datos", 500)

    try:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT o.*, p.nombre AS paciente_nombre, p.apellidos AS paciente_apellidos
            FROM orden_laboratorio o
            LEFT JOIN paciente p ON p.id_paciente = o.id_paciente
            ORDER BY o.fecha_solicitud DESC, o.id_orden DESC
            """
        )
        return api_ok({"ordenes": rows_to_dicts(cursor, cursor.fetchall())})
    except Exception as exc:
        return api_error(str(exc), 500)
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()


def crear_orden(data=None):
    data = data or request_data()
    fecha_orden = data.get("fecha_solicitud") or data.get("fecha")
    required = ["id_paciente", "tipo_estudio", "medico", "especialidad", "descripcion"]
    missing = [field for field in required if not data.get(field)]
    if not fecha_orden:
        missing.append("fecha_solicitud")
    if missing:
        return api_error("Campos obligatorios faltantes: " + ", ".join(missing), 400)

    conexion = get_db_connection()
    if not conexion:
        return api_error("Error de conexion a la base de datos", 500)

    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT id_paciente FROM paciente WHERE id_paciente = %s", (data.get("id_paciente"),))
        if not cursor.fetchone():
            return api_error("Paciente no encontrado.", 404, "ERR-01")

        insert_dynamic(
            cursor,
            "orden_laboratorio",
            {
                "id_paciente": data.get("id_paciente"),
                "id_medico": data.get("id_medico") or data.get("medico_id") or 1,
                "tipo_estudio": data.get("tipo_estudio"),
                "fecha_solicitud": fecha_orden,
                "fecha": fecha_orden,
                "medico": data.get("medico"),
                "especialidad": data.get("especialidad"),
                "descripcion": data.get("descripcion"),
                "estado": "Solicitado",
            },
        )
        id_orden = cursor.lastrowid
        folio = f"EST-{id_orden:04d}"
        update_dynamic(cursor, "orden_laboratorio", "id_orden", id_orden, {"folio": folio})
        conexion.commit()
        return api_ok({"mensaje": "Orden registrada.", "id_orden": id_orden, "folio": folio, "estado": "Solicitado"}, 201)
    except Exception as exc:
        conexion.rollback()
        return api_error(str(exc), 500)
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()


def agendar_cita_laboratorio(data=None):
    data = data or request_data()
    required = ["id_orden", "fecha_consulta", "fecha_laboratorio", "hora"]
    missing = [field for field in required if not data.get(field)]
    if missing:
        return api_error("Campos obligatorios faltantes: " + ", ".join(missing), 400)

    try:
        diff_days = _days_between(data.get("fecha_laboratorio"), data.get("fecha_consulta"))
    except ValueError:
        return api_error("Formato de fecha invalido. Use YYYY-MM-DD.", 400)

    if diff_days < 7 or diff_days > 14:
        return api_error(
            "Error de temporalidad: El estudio debe agendarse entre 1 y 2 semanas antes de la consulta medica.",
            409,
            "ERR-06",
        )

    conexion = get_db_connection()
    if not conexion:
        return api_error("Error de conexion a la base de datos", 500)

    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT id_orden FROM orden_laboratorio WHERE id_orden = %s", (data.get("id_orden"),))
        if not cursor.fetchone():
            return api_error("Orden de laboratorio no encontrada.", 404, "ERR-04")

        insert_dynamic(
            cursor,
            "cita_laboratorio",
            {
                "id_orden": data.get("id_orden"),
                "fecha_consulta": data.get("fecha_consulta"),
                "fecha_laboratorio": data.get("fecha_laboratorio"),
                "hora": data.get("hora"),
                "estado": "Programada",
            },
        )
        conexion.commit()
        return api_ok({"mensaje": "Cita de laboratorio registrada.", "id_cita_laboratorio": cursor.lastrowid}, 201)
    except Exception as exc:
        conexion.rollback()
        return api_error(str(exc), 500)
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()


def capturar_resultados(data=None):
    data = data or request_data()
    id_orden = data.get("id_orden") or data.get("folio")
    resultados = data.get("resultados") or data.get("resultadosAnaliticos") or {}
    observaciones = data.get("observaciones")
    if not id_orden:
        return api_error("Error: No se puede registrar el resultado porque el detalle de la orden de laboratorio no existe.", 404, "MSG-06")

    conexion = get_db_connection()
    if not conexion:
        return api_error("Error de conexion a la base de datos", 500)

    try:
        cursor = conexion.cursor()
        if isinstance(id_orden, str) and id_orden.upper().startswith("EST-"):
            cursor.execute("SELECT id_orden, estado FROM orden_laboratorio WHERE UPPER(folio) = %s", (id_orden.upper(),))
        else:
            cursor.execute("SELECT id_orden, estado FROM orden_laboratorio WHERE id_orden = %s", (id_orden,))
        orden = cursor.fetchone()
        if not orden:
            return api_error("Error: No se puede registrar el resultado porque el detalle de la orden de laboratorio no existe.", 404, "MSG-06")
        if orden[1] == "Liberado":
            return api_error("El estudio ya fue liberado y no admite modificaciones.", 409, "RN-04")

        insert_dynamic(
            cursor,
            "resultado_laboratorio",
            {
                "id_orden": orden[0],
                "resultados_json": json.dumps(resultados, ensure_ascii=False),
                "observaciones": observaciones,
            },
        )
        update_dynamic(cursor, "orden_laboratorio", "id_orden", orden[0], {"estado": "Realizado"})
        conexion.commit()
        return api_ok({"mensaje": "Resultados guardados.", "estado": "Realizado"}, 201)
    except Exception as exc:
        conexion.rollback()
        return api_error(str(exc), 500)
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()


def liberar_resultados(data=None):
    data = data or request_data()
    folio = data.get("folio")
    id_orden = data.get("id_orden")
    if not folio and not id_orden:
        return api_error("Error: No se puede registrar el resultado. Verifique que exista la orden de laboratorio.", 404, "ERR-04")

    conexion = get_db_connection()
    if not conexion:
        return api_error("Error de conexion a la base de datos", 500)

    try:
        cursor = conexion.cursor()
        if folio:
            cursor.execute("SELECT id_orden, estado FROM orden_laboratorio WHERE UPPER(folio) = %s", (folio.upper(),))
        else:
            cursor.execute("SELECT id_orden, estado FROM orden_laboratorio WHERE id_orden = %s", (id_orden,))
        orden = cursor.fetchone()
        if not orden:
            return api_error("Error: No se puede registrar el resultado. Verifique que exista la orden de laboratorio.", 404, "ERR-04")
        if orden[1] == "Liberado":
            return api_error("El estudio ya fue liberado y no admite modificaciones.", 409, "RN-04")
        if orden[1] not in ("Realizado", "Solicitado"):
            return api_error("Solo pueden liberarse estudios solicitados o realizados.", 409)

        update_dynamic(cursor, "orden_laboratorio", "id_orden", orden[0], {"estado": "Liberado"})
        conexion.commit()
        return api_ok({"mensaje": "Resultados de laboratorio guardados y liberados al expediente digital de forma exitosa.", "estado": "Liberado"})
    except Exception as exc:
        conexion.rollback()
        return api_error(str(exc), 500)
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()


def cancelar_estudio(id):
    conexion = get_db_connection()
    if not conexion:
        return api_error("Error de conexion a la base de datos", 500)

    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT estado FROM orden_laboratorio WHERE id_orden = %s", (id,))
        orden = cursor.fetchone()
        if not orden:
            return api_error("Orden de laboratorio no encontrada.", 404)
        if orden[0] == "Liberado":
            return api_error("Un estudio liberado no puede cancelarse.", 409, "RN-04")
        update_dynamic(cursor, "orden_laboratorio", "id_orden", id, {"estado": "Cancelado"})
        conexion.commit()
        return api_ok({"mensaje": "El registro ha sido cancelado y actualizado correctamente en el historial.", "codigo": "MSG-07"})
    except Exception as exc:
        conexion.rollback()
        return api_error(str(exc), 500)
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()


def consultar_expediente(id_paciente):
    conexion = get_db_connection()
    if not conexion:
        return api_error("Error de conexion a la base de datos", 500)

    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM paciente WHERE id_paciente = %s", (id_paciente,))
        paciente = row_to_dict(cursor, cursor.fetchone())
        if not paciente:
            return api_error("Paciente no encontrado.", 404, "ERR-01")

        cursor.execute(
            """
            SELECT o.*, r.resultados_json, r.observaciones, r.fecha_registro
            FROM orden_laboratorio o
            LEFT JOIN resultado_laboratorio r ON r.id_orden = o.id_orden
            WHERE o.id_paciente = %s
            ORDER BY o.fecha_solicitud DESC, o.id_orden DESC
            """,
            (id_paciente,),
        )
        return api_ok({"paciente": paciente, "estudios": rows_to_dicts(cursor, cursor.fetchall()), "solo_lectura": True})
    except Exception as exc:
        return api_error(str(exc), 500)
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()


def reportes_basicos():
    conexion = get_db_connection()
    if not conexion:
        return api_error("Error de conexion a la base de datos", 500)

    try:
        cursor = conexion.cursor()
        report = {}
        for table, key in (("cita", "citas_por_estado"), ("orden_laboratorio", "estudios_por_estado")):
            cursor.execute(f"SELECT estado, COUNT(*) FROM {table} GROUP BY estado")
            report[key] = {estado: count for estado, count in cursor.fetchall()}
        return api_ok(report)
    except Exception as exc:
        return api_error(str(exc), 500)
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()
