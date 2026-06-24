from flask import Blueprint

from controllers.common import require_roles, request_data
from controllers.medicos_controller import (
    actualizar_medico,
    crear_medico,
    eliminar_medico,
    obtener_medico,
    obtener_medicos,
)


medicos_bp = Blueprint("medicos", __name__)


@medicos_bp.route("", methods=["GET"])
@medicos_bp.route("/", methods=["GET"])
@require_roles("recepcionista")
def get_medicos():
    return obtener_medicos()


@medicos_bp.route("/<int:id>", methods=["GET"])
@require_roles("recepcionista")
def get_medico(id):
    return obtener_medico(id)


@medicos_bp.route("", methods=["POST"])
@medicos_bp.route("/", methods=["POST"])
@require_roles("recepcionista")
def post_medico():
    return crear_medico(request_data())


@medicos_bp.route("/<int:id>", methods=["PUT", "PATCH"])
@require_roles("recepcionista")
def put_medico(id):
    return actualizar_medico(id, request_data())


@medicos_bp.route("/<int:id>", methods=["DELETE"])
@require_roles("recepcionista")
def delete_medico(id):
    return eliminar_medico(id)
