from flask import Blueprint

from controllers.common import require_roles
from controllers.laboratorio_controller import (
    agendar_cita_laboratorio,
    cancelar_estudio,
    capturar_resultados,
    consultar_expediente,
    crear_orden,
    liberar_resultados,
    obtener_ordenes,
    reportes_basicos,
)


laboratorio_bp = Blueprint("laboratorio", __name__)


@laboratorio_bp.route("/ordenes", methods=["GET"])
@require_roles("laboratorista")
def get_ordenes():
    return obtener_ordenes()


@laboratorio_bp.route("/ordenes", methods=["POST"])
@require_roles("laboratorista")
def post_orden():
    return crear_orden()


@laboratorio_bp.route("/ordenes/<int:id>", methods=["DELETE"])
@require_roles("laboratorista")
def delete_orden(id):
    return cancelar_estudio(id)


@laboratorio_bp.route("/citas-laboratorio", methods=["POST"])
@require_roles("recepcionista")
def post_cita_laboratorio():
    return agendar_cita_laboratorio()


@laboratorio_bp.route("/resultados", methods=["POST"])
@require_roles("laboratorista")
def post_resultados():
    return capturar_resultados()


@laboratorio_bp.route("/resultados/liberar", methods=["PUT", "PATCH"])
@require_roles("laboratorista")
def put_liberar_resultados():
    return liberar_resultados()


@laboratorio_bp.route("/expedientes/<int:id_paciente>", methods=["GET"])
@require_roles("recepcionista", "laboratorista")
def get_expediente(id_paciente):
    return consultar_expediente(id_paciente)


@laboratorio_bp.route("/reportes", methods=["GET"])
@require_roles("recepcionista", "laboratorista")
def get_reportes():
    return reportes_basicos()
