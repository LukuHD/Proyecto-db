from flask import Blueprint

from controllers.common import require_roles
from controllers.pacientes_controller import (
    actualizar_paciente,
    buscar_pacientes,
    cancelar_paciente,
    crear_paciente,
    obtener_paciente,
)


pacientes_bp = Blueprint("pacientes", __name__)


@pacientes_bp.route("", methods=["POST"])
@pacientes_bp.route("/", methods=["POST"])
@require_roles("recepcionista")
def registrar_paciente():
    return crear_paciente()


@pacientes_bp.route("", methods=["GET"])
@pacientes_bp.route("/", methods=["GET"])
@require_roles("recepcionista", "laboratorista")
def buscar():
    return buscar_pacientes()


@pacientes_bp.route("/<int:id>", methods=["GET"])
@require_roles("recepcionista", "laboratorista")
def obtener(id):
    return obtener_paciente(id)


@pacientes_bp.route("/<int:id>", methods=["PUT", "PATCH"])
@require_roles("recepcionista")
def actualizar(id):
    return actualizar_paciente(id)


@pacientes_bp.route("/<int:id>", methods=["DELETE"])
@require_roles("recepcionista")
def cancelar(id):
    return cancelar_paciente(id)
