from flask import Blueprint

from controllers.citas_controller import (
    actualizar_cita,
    agenda_medicos,
    crear_cita,
    eliminar_cita,
    obtener_cita,
    obtener_citas,
)
from controllers.common import require_roles, request_data


citas_bp = Blueprint("citas", __name__)


@citas_bp.route("", methods=["GET"])
@citas_bp.route("/", methods=["GET"])
@require_roles("recepcionista")
def get_citas():
    return obtener_citas()


@citas_bp.route("", methods=["POST"])
@citas_bp.route("/", methods=["POST"])
@require_roles("recepcionista")
def post_cita():
    return crear_cita(request_data())


@citas_bp.route("/<int:id>", methods=["GET"])
@require_roles("recepcionista")
def get_cita(id):
    return obtener_cita(id)


@citas_bp.route("/<int:id>", methods=["PUT", "PATCH"])
@require_roles("recepcionista")
def put_cita(id):
    return actualizar_cita(id, request_data())


@citas_bp.route("/<int:id>", methods=["DELETE"])
@require_roles("recepcionista")
def delete_cita(id):
    return eliminar_cita(id)


@citas_bp.route("/agenda", methods=["GET", "POST"])
@require_roles("recepcionista")
def get_agenda():
    return agenda_medicos()
