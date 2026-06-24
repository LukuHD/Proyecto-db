from functools import wraps

from flask import jsonify, request, session


def api_error(message, status=400, code=None):
    payload = {"error": message}
    if code:
        payload["codigo"] = code
    return jsonify(payload), status


def api_ok(payload=None, status=200):
    return jsonify(payload or {}), status


def request_data():
    return request.get_json(silent=True) or {}


def current_role():
    return session.get("rol") or request.headers.get("X-Rol") or request.headers.get("X-Role")


def require_roles(*allowed_roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            role = current_role()
            if not role:
                return api_error("Acceso denegado: sesion requerida.", 401, "RN-08")
            if role not in allowed_roles:
                return api_error("Acceso denegado: rol no autorizado para esta operacion.", 403, "RN-08")
            return func(*args, **kwargs)

        return wrapper

    return decorator


def table_columns(cursor, table_name):
    cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
    return {row[0] for row in cursor.fetchall()}


def insert_dynamic(cursor, table_name, values):
    columns = table_columns(cursor, table_name)
    data = {key: value for key, value in values.items() if key in columns}
    if not data:
        raise ValueError(f"No hay columnas compatibles para insertar en {table_name}.")

    field_sql = ", ".join(f"`{key}`" for key in data)
    placeholder_sql = ", ".join(["%s"] * len(data))
    cursor.execute(
        f"INSERT INTO `{table_name}` ({field_sql}) VALUES ({placeholder_sql})",
        tuple(data.values()),
    )


def update_dynamic(cursor, table_name, record_id_column, record_id, values):
    columns = table_columns(cursor, table_name)
    data = {key: value for key, value in values.items() if key in columns and value is not None}
    if not data:
        raise ValueError(f"No hay columnas compatibles para actualizar en {table_name}.")

    set_sql = ", ".join(f"`{key}` = %s" for key in data)
    cursor.execute(
        f"UPDATE `{table_name}` SET {set_sql} WHERE `{record_id_column}` = %s",
        tuple(data.values()) + (record_id,),
    )


def row_to_dict(cursor, row):
    if row is None:
        return None
    return {desc[0]: value for desc, value in zip(cursor.description, row)}


def rows_to_dicts(cursor, rows):
    return [row_to_dict(cursor, row) for row in rows]
